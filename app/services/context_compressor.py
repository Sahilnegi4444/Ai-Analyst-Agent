from app.providers.llm import GroqLLMProvider
from app.config import settings

class ContextCompressor:
    """
    Service class responsible for summarizing retrieved document chunks to 100-150 tokens.
    Leverages a fast, low-cost Llama-3.1-8b model via Groq API.
    """
    def __init__(self):
        self.client = GroqLLMProvider()
        self.model = settings.GROQ_SQL_MODEL # Llama-3.1-8b-instant

    def compress_chunk(self, query: str, chunk_text: str) -> dict:
        """
        Compresses a text chunk focusing only on query-relevant facts.
        Returns a dict with 'compressed_text', 'prompt_tokens', and 'completion_tokens'.
        """
        system_prompt = (
            "You are a text compression utility. Your job is to compress the provided document chunk "
            "into a highly concise, factual summary of 100 to 150 tokens max.\n"
            "Rules:\n"
            "- Extract ONLY dates, numbers, metrics, rules, and facts directly relevant to the user query.\n"
            "- Avoid preambles, greetings, or conversational filler.\n"
            "- If the text contains no query-relevant info, return: 'No relevant information in this chunk.'\n"
            "- Output ONLY the raw compressed text. No explanations."
        )

        user_content = f"User Query: \"{query}\"\n\nDocument Chunk:\n{chunk_text}\n\nCompressed Text:"

        try:
            response = self.client.generate(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                model=self.model,
                temperature=0.0
            )

            compressed_text = response.choices[0].message.content.strip()
            return {
                "compressed_text": compressed_text,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens
            }
        except Exception as e:
            print(f"[WARNING] RAG compression failed: {e}. Falling back to original chunk.")
            return {
                "compressed_text": chunk_text,
                "prompt_tokens": 0,
                "completion_tokens": 0
            }
