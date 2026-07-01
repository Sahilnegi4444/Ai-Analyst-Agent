import os
import json
import logging
from datetime import datetime
from typing import List, Optional

# Configure standard console logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AiDataAnalyst")

class ObservabilityLogger:
    """
    Utility class handling application observability and diagnostic tracing.
    Saves detailed transaction states into a JSON-Lines file for production audits.
    """
    LOG_FILE = "data/observability_runs.jsonl"

    @classmethod
    def log_agent_run(
        cls,
        user_query: str,
        detected_intent: str,
        selected_tools: List[str],
        generated_sql: Optional[str],
        execution_status: str,
        retrieval_results: Optional[List[dict]],
        latency: float,
        cached: bool = False,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        sql_latency: float = 0.0,
        retrieval_latency: float = 0.0,
        analytics_latency: float = 0.0
    ):
        # Format the log record
        log_record = {
            "timestamp": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            "user_query": user_query,
            "detected_intent": detected_intent,
            "selected_tools": selected_tools,
            "generated_sql": generated_sql,
            "execution_status": execution_status,
            "rag_chunks_count": len(retrieval_results) if retrieval_results else 0,
            "latency_seconds": round(latency, 4),
            "cached": cached,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "sql_latency_seconds": round(sql_latency, 4),
            "retrieval_latency_seconds": round(retrieval_latency, 4),
            "analytics_latency_seconds": round(analytics_latency, 4)
        }

        # 1. Output to standard console logs
        logger.info(
            f"[AGENT RUN] Intent: {detected_intent} | Status: {execution_status} | "
            f"Tools: {selected_tools} | Latency: {latency:.4f}s | Cached: {cached} | "
            f"Tokens: {prompt_tokens}p + {completion_tokens}c = {prompt_tokens + completion_tokens}"
        )
        if generated_sql:
            logger.info(f"[SQL GENERATED] {generated_sql}")

        # 2. Append to structured log file (development) or stream to stdout (production)
        if os.getenv("ENVIRONMENT", "development") == "development":
            try:
                # Ensure data folder exists
                os.makedirs(os.path.dirname(cls.LOG_FILE), exist_ok=True)
                with open(cls.LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(log_record) + "\n")
            except Exception as e:
                logger.error(f"Failed to write observability log: {e}")
        else:
            # Stream JSON-lines directly to stdout for production log aggregation
            print(f"[OBSERVABILITY RUN LOG] {json.dumps(log_record)}")
