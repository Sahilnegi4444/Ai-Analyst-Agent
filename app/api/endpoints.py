import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse, SourceAttribution
from app.schemas.documents import DocumentMetadata, DocumentListResponse, DocumentUploadResponse
from app.schemas.analytics import AnalyticsReport, SalesSummary, InventorySummary
from app.agents.workflow import AgentExecutor
from app.services.analytics_service import AnalyticsService
from app.services.ingestion import IngestionService
from app.models import DocumentChunk
from sqlalchemy import func

router = APIRouter()

# =====================================================================
# CHAT ENDPOINT
# =====================================================================
@router.post("/chat", response_model=ChatResponse)
def chat_with_agent(request: ChatRequest):
    """
    Primary agent interface. Classifies query intent, routes to appropriate SQL,
    RAG, or Analytics tools, and synthesizes a factual business answer.
    """
    try:
        # Invoke LangGraph Agent workflow
        res = AgentExecutor.run(request.query)
        
        # Format source attributions if RAG chunks are present
        sources = None
        if res.get("rag_chunks"):
            sources = [
                SourceAttribution(
                    filename=c["filename"],
                    title=c["title"],
                    content_snippet=c["content"],
                    confidence=c["confidence"]
                ) for c in res["rag_chunks"]
            ]

        return ChatResponse(
            query=res["query"],
            intent=res["intent"].get("intent", "UNKNOWN"),
            final_response=res["final_response"],
            status=res["status"],
            sql_generated=res.get("sql_query"),
            sql_results=res.get("sql_results"),
            sources=sources,
            latency_seconds=res.get("latency", 0.0),
            cached=res.get("cached", False)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent runtime failure: {e}")

# =====================================================================
# DOCUMENT UPLOAD & MANAGEMENT ENDPOINTS
# =====================================================================
@router.post("/documents/upload", response_model=DocumentUploadResponse)
def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Accepts PDF file, saves it to storage directory, chunks it,
    computes embeddings, and index-stores it for RAG.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF documents are supported.")
        
    doc_folder = "data/documents"
    os.makedirs(doc_folder, exist_ok=True)
    
    file_path = os.path.join(doc_folder, file.filename)
    try:
        # Save uploaded file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Trigger parsing and vector ingestion
        ingestion = IngestionService(db)
        
        # Check current chunk count to compute delta
        prev_count = db.query(DocumentChunk).filter(DocumentChunk.filename == file.filename).count()
        if prev_count > 0:
            # Delete old chunks to allow clean override
            db.query(DocumentChunk).filter(DocumentChunk.filename == file.filename).delete()
            db.commit()
            
        ingestion.ingest_pdf_documents(doc_folder)
        
        new_count = db.query(DocumentChunk).filter(DocumentChunk.filename == file.filename).count()
        
        return DocumentUploadResponse(
            filename=file.filename,
            chunks_count=new_count,
            status="success"
        )
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {e}")

@router.get("/documents", response_model=DocumentListResponse)
def list_documents(db: Session = Depends(get_db)):
    """
    Lists metadata and chunk counts for all indexed documents in the RAG store.
    """
    try:
        # Group by filename to get metadata counts
        grouped = (
            db.query(
                DocumentChunk.filename,
                DocumentChunk.title,
                func.count(DocumentChunk.id).label("chunks")
            )
            .group_by(DocumentChunk.filename, DocumentChunk.title)
            .all()
        )
        
        docs = [
            DocumentMetadata(
                filename=row[0],
                title=row[1],
                chunks_count=row[2]
            ) for row in grouped
        ]
        return DocumentListResponse(documents=docs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failure: {e}")

# =====================================================================
# BUSINESS METRIC ENDPOINTS
# =====================================================================
@router.get("/sales", response_model=SalesSummary)
def get_sales_summary():
    """
    Returns high-level sales KPI summaries computed from database sales records.
    """
    try:
        service = AnalyticsService()
        kpis = service.calculate_sales_summary()
        return SalesSummary(**kpis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute sales analytics: {e}")

@router.get("/inventory", response_model=InventorySummary)
def get_inventory_summary():
    """
    Returns inventory health and supplier metrics from current database status.
    """
    try:
        service = AnalyticsService()
        kpis = service.calculate_inventory_summary()
        return InventorySummary(**kpis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute inventory analytics: {e}")

# =====================================================================
# SYSTEM ANALYTICS REPORT ENDPOINT
# =====================================================================
@router.get("/analytics/report", response_model=AnalyticsReport)
def get_analytics_report():
    """
    Generates a full mathematical business performance report.
    Calculates sales metrics, inventory health, monthly trends, and MoM growth.
    """
    try:
        service = AnalyticsService()
        sales_kpi = service.calculate_sales_summary()
        inv_kpi = service.calculate_inventory_summary()
        distribution = service.calculate_monthly_sales_distribution()
        growth = service.calculate_month_over_month_growth()
        
        return AnalyticsReport(
            sales=SalesSummary(**sales_kpi),
            inventory=InventorySummary(**inv_kpi),
            monthly_sales_distribution=distribution,
            month_over_month_growth=growth
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compile analytics report: {e}")
