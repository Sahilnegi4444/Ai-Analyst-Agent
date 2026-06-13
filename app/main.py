import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environmental configs from dotenv
load_dotenv()

from app.api.endpoints import router as api_router
from app.config import settings

# Initialize FastAPI App
app = FastAPI(
    title="Production AI Data Analyst Agent API",
    description=(
        "An enterprise-ready Business Intelligence and Analytics platform. "
        "Allows natural language SQL execution, document RAG retrieval, "
        "and strict Pandas-based analytics computations."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this to target hosts in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint for health check
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
