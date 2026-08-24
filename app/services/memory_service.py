import datetime
from typing import Any

from groq import Groq
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.models import ChatMessage


class ChatMemoryService:
    """
    Service responsible for loading conversation history, rewriting/contextualizing
    user follow-up queries using Groq, and storing conversation logs in PostgreSQL.
    """
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_ROUTER_MODEL  # gpt-oss-20b (fast and low-cost)

    def get_history(self, db: Session, session_id: str, limit: int = 10) -> list[ChatMessage]:
        """
        Retrieves the last N messages for a given session ID in chronological order.
        """
        return (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.timestamp.asc())
            .limit(limit)
            .all()
        )

    def add_message(
        self,
        db: Session,
        session_id: str,
        sender: str,
        text: str,
        intent: str | None = None,
        sql_generated: str | None = None,
        sql_results: list[dict[str, Any]] | None = None,
        sources: list[dict[str, Any]] | None = None,
        latency_seconds: float | None = None,
        cached: bool | None = None,
        status: str | None = None
    ) -> ChatMessage:
        """
        Appends a user query or agent response to the session history in PostgreSQL.
        """
        try:
            msg = ChatMessage(
                session_id=session_id,
                sender=sender,
                text=text,
                intent=intent,
                sql_generated=sql_generated,
                sql_results=sql_results,
                sources=sources,
                latency_seconds=latency_seconds,
                cached=cached,
                status=status,
                timestamp=datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)
            return msg
        except Exception as e:
            db.rollback()
            print(f"[ERROR] Failed to save chat message: {e}")
            raise

    def contextualize_query(self, query: str, history: list[ChatMessage]) -> str:
        """
        Uses an LLM to rewrite a user query, injecting context from the history
        so that the query is self-contained. E.g.:
        "Show suppliers from Germany" -> "What is their average rating?"
        becomes "What is the average rating of suppliers from Germany?".
        """
        # If there is no prior history, the query does not need rewriting.
        if not history:
            return query

        system_prompt = (
            "You are a query contextualization utility.\n"
            "Your job is to analyze the conversation history and the latest user query, "
            "and rewrite the query to be a self-contained, descriptive question that resolves any pronoun "
            "references or implicit context (such as active time periods, suppliers, products, or locations).\n"
            "Rules:\n"
            "- Resolve pronouns (e.g., 'they', 'their', 'it', 'them') based on the preceding turns.\n"
            "- Focus only on clarifying reference ambiguities. Keep the intent and substance of the user query identical.\n"
            "- If the latest query is already fully self-contained and does not refer back to past context, return it exactly as-is.\n"
            "- Do NOT answer the question. Only output the rewritten question.\n"
            "- Do NOT wrap the output in quotes, markdown, or code blocks.\n"
            "- Do NOT add any preamble, explanations, or conversational filler."
        )

        history_lines = []
        for msg in history:
            role = "User" if msg.sender == "user" else "Assistant"
            history_lines.append(f"{role}: {msg.text}")

        history_str = "\n".join(history_lines)
        user_content = f"Conversation History:\n{history_str}\n\nLatest Query: \"{query}\"\n\nRewritten Query:"

        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                model=self.model,
                temperature=0.0
            )
            rewritten = response.choices[0].message.content.strip()
            # Clean up potential leading/trailing quotes from LLM
            if rewritten.startswith('"') and rewritten.endswith('"') or rewritten.startswith("'") and rewritten.endswith("'"):
                rewritten = rewritten[1:-1].strip()

            print(f"[CONTEXTUALIZER] Original: '{query}' -> Rewritten: '{rewritten}'")
            return rewritten if rewritten else query
        except Exception as e:
            print(f"[WARNING] Query contextualization failed: {e}. Using original query.")
            return query

    def get_sessions(self, db: Session) -> list[str]:
        """
        Retrieves unique session IDs in descending order of their latest activity.
        """
        subquery = (
            db.query(
                ChatMessage.session_id,
                func.max(ChatMessage.timestamp).label("last_activity")
            )
            .group_by(ChatMessage.session_id)
            .subquery()
        )

        rows = (
            db.query(subquery.c.session_id)
            .order_by(subquery.c.last_activity.desc())
            .all()
        )

        return [row[0] for row in rows]

    def delete_session(self, db: Session, session_id: str):
        """
        Deletes all message history records associated with a session ID.
        """
        try:
            db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[ERROR] Failed to delete session: {e}")
            raise
