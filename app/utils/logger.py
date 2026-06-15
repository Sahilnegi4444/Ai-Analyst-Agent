import os
import json
import logging
from datetime import datetime
from typing import List, Optional, Any

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
        cached: bool = False
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
            "cached": cached
        }

        # 1. Output to standard console logs
        logger.info(
            f"[AGENT RUN] Intent: {detected_intent} | Status: {execution_status} | "
            f"Tools: {selected_tools} | Latency: {latency:.4f}s | Cached: {cached}"
        )
        if generated_sql:
            logger.info(f"[SQL GENERATED] {generated_sql}")

        # 2. Append to structured log file
        try:
            # Ensure data folder exists
            os.makedirs(os.path.dirname(cls.LOG_FILE), exist_ok=True)
            
            with open(cls.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_record) + "\n")
        except Exception as e:
            logger.error(f"Failed to write observability log: {e}")
