import os

# Cap internal thread pools to 1 to prevent deadlock/starvation
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy import text

from app.api.endpoints import router as api_router
from app.config import settings
from app.database import engine
from app.services.cache_service import RedisCacheService

# Load environmental configs from dotenv
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    yield
    # Shutdown logic (gracefully close connection pools)
    print("Shutting down backend server. Disposing database connections...")
    engine.dispose()

# Initialize FastAPI App with lifespan context
app = FastAPI(
    title="Production AI Data Analyst Agent API",
    description=(
        "An enterprise-ready Business Intelligence and Analytics platform. "
        "Allows natural language SQL execution, document RAG retrieval, "
        "and strict Pandas-based analytics computations."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health endpoint (liveness check)
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

# Readiness endpoint (dependency check)
@app.get("/ready")
def readiness_check():
    checks = {}
    
    # 1. Database Connection check
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {e}"
        
    # 2. Redis Connection check
    try:
        cache_service = RedisCacheService()
        if cache_service.enabled:
            cache_service.client.ping()
            checks["redis"] = "healthy"
        elif cache_service.memory_fallback:
            checks["redis"] = "fallback_active (in-memory)"
        else:
            checks["redis"] = "disabled"
    except Exception as e:
        checks["redis"] = f"unhealthy: {e}"
        
    # If the core database check fails, return 503 Service Unavailable
    if "unhealthy" in checks["database"]:
        raise HTTPException(status_code=503, detail={"status": "unready", "checks": checks})
        
    return {
        "status": "ready",
        "checks": checks
    }

# Root endpoint for general service description
@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "AI Data Analyst Agent backend",
        "documentation_docs": "/docs",
        "database_connected": bool(settings.DATABASE_URL)
    }

# Include API endpoints router
app.include_router(api_router, prefix="/api/v1" if False else "")
