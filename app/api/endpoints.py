import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    SourceAttribution,
    MessageHistoryResponse,
    MessageHistoryItem,
    SessionListResponse
)
from app.schemas.documents import DocumentMetadata, DocumentListResponse, DocumentUploadResponse
from app.schemas.analytics import AnalyticsReport, SalesSummary, InventorySummary
from app.agents.workflow import AgentExecutor
from app.services.analytics_service import AnalyticsService
from app.services.ingestion import IngestionService
from app.models import DocumentChunk
from sqlalchemy import func

router = APIRouter()

# =====================================================================
# CHAT ENDPOINTS
# =====================================================================
@router.post("/chat", response_model=ChatResponse)
def chat_with_agent(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Primary agent interface. Classifies query intent, routes to appropriate SQL,
    RAG, or Analytics tools, and synthesizes a factual business answer.
    """
    try:
        from app.services.memory_service import ChatMemoryService
        memory_service = ChatMemoryService()

        # 1. Resolve session_id and load history
        session_id = request.session_id or "default_session"
        history = memory_service.get_history(db, session_id, limit=10)

        # 2. Contextualize/rewrite the user query
        processed_query = memory_service.contextualize_query(request.query, history)

        # 3. Save User message to history
        memory_service.add_message(db, session_id=session_id, sender="user", text=request.query)

        # 4. Invoke LangGraph Agent workflow using the contextualized/rewritten query
        res = AgentExecutor.run(processed_query)
        
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

        # 5. Save Agent response to history
        sources_dict = None
        if res.get("rag_chunks"):
            sources_dict = [
                {
                    "filename": c["filename"],
                    "title": c["title"],
                    "content_snippet": c["content"],
                    "confidence": c["confidence"]
                } for c in res["rag_chunks"]
            ]

        memory_service.add_message(
            db,
            session_id=session_id,
            sender="agent",
            text=res["final_response"],
            intent=res["intent"].get("intent", "UNKNOWN"),
            sql_generated=res.get("sql_query"),
            sql_results=res.get("sql_results"),
            sources=sources_dict,
            latency_seconds=res.get("latency", 0.0),
            cached=res.get("cached", False),
            status=res["status"]
        )

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

@router.get("/sessions", response_model=SessionListResponse)
def list_chat_sessions(db: Session = Depends(get_db)):
    """
    Returns a list of unique session IDs sorted by their latest activity.
    """
    try:
        from app.services.memory_service import ChatMemoryService
        memory_service = ChatMemoryService()
        sessions = memory_service.get_sessions(db)
        return SessionListResponse(sessions=sessions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load sessions: {e}")

@router.get("/sessions/{session_id}/messages", response_model=MessageHistoryResponse)
def get_session_message_history(session_id: str, db: Session = Depends(get_db)):
    """
    Returns the full chronological message log for a specific session.
    """
    try:
        from app.services.memory_service import ChatMemoryService
        memory_service = ChatMemoryService()
        history = memory_service.get_history(db, session_id, limit=50) # Return up to 50 messages
        
        items = []
        for msg in history:
            sources = None
            if msg.sources:
                sources = [
                    SourceAttribution(
                        filename=s["filename"],
                        title=s["title"],
                        content_snippet=s["content_snippet"],
                        confidence=s["confidence"]
                    ) for s in msg.sources
                ]
            
            items.append(
                MessageHistoryItem(
                    id=msg.id,
                    session_id=msg.session_id,
                    sender=msg.sender,
                    text=msg.text,
                    intent=msg.intent,
                    sql_generated=msg.sql_generated,
                    sql_results=msg.sql_results,
                    sources=sources,
                    latency_seconds=float(msg.latency_seconds) if msg.latency_seconds is not None else None,
                    cached=msg.cached,
                    status=msg.status,
                    timestamp=msg.timestamp
                )
            )
        return MessageHistoryResponse(messages=items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch session history: {e}")

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
    
    # Extract only the base name to prevent path traversal/injection
    safe_filename = os.path.basename(file.filename)
    if not safe_filename or safe_filename in ('.', '..'):
        raise HTTPException(status_code=400, detail="Invalid filename.")
        
    file_path = os.path.join(doc_folder, safe_filename)
    try:
        # Save uploaded file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Trigger parsing and vector ingestion
        ingestion = IngestionService(db)
        
        # Check current chunk count to compute delta
        prev_count = db.query(DocumentChunk).filter(DocumentChunk.filename == safe_filename).count()
        if prev_count > 0:
            # Delete old chunks to allow clean override
            db.query(DocumentChunk).filter(DocumentChunk.filename == safe_filename).delete()
            db.commit()
            
        ingestion.ingest_pdf_documents(doc_folder)
        
        new_count = db.query(DocumentChunk).filter(DocumentChunk.filename == safe_filename).count()
        
        return DocumentUploadResponse(
            filename=safe_filename,
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
