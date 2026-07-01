import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://analyst_user:analyst_password@localhost:5432/ai_analyst_db"
    )
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    RERANK_MODEL_NAME: str = os.getenv("RERANK_MODEL_NAME", "cross-encoder/ettin-reranker-17m-v1")
    GROQ_ROUTER_MODEL: str = os.getenv("GROQ_ROUTER_MODEL", "llama-3.1-8b-instant")
    GROQ_SQL_MODEL: str = os.getenv("GROQ_SQL_MODEL", "llama-3.1-8b-instant")
    GROQ_GENERATOR_MODEL: str = os.getenv("GROQ_GENERATOR_MODEL", "llama-3.3-70b-versatile")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_CACHE_TTL: int = int(os.getenv("REDIS_CACHE_TTL", "3600"))

settings = Settings()
