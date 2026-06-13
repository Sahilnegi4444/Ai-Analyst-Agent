from sqlalchemy.orm import Session
from app.repositories import DocumentRepository
from app.services.embedding import EmbeddingService
from typing import List, Dict, Any

class RAGTool:
    """
    Tool responsible for performing vector similarity search on ingested PDF documents
    and returning the most relevant chunks with source attribution and confidence scores.
    """
    def __init__(self, db: Session):
        self.db = db
        self.doc_repository = DocumentRepository(db)
        self.embedding_service = EmbeddingService()

    def retrieve_context(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Generates query vector embedding and searches document database for top-k matches.
        
        Returns:
            dict: Containing 'chunks' (list of text chunks with metadata) and 'status'.
        """
        try:
            # 1. Generate search query embedding
            query_vector = self.embedding_service.get_embedding(query)

            # 2. Query documents using pgvector cosine similarity search
            similar_chunks = self.doc_repository.search_similar(query_vector, limit=top_k)

            # 3. Format results with source attribution and confidence score
            results = []
            for chunk, distance in similar_chunks:
                # Cosine similarity = 1.0 - cosine_distance
                confidence = round(1.0 - distance, 4)
                
                results.append({
                    "filename": chunk.filename,
                    "title": chunk.title,
                    "content": chunk.content,
                    "confidence": confidence
                })

            return {
                "status": "success",
                "chunks": results,
                "error": None
            }
        except Exception as e:
            print(f"[ERROR] RAG Retrieval failure: {e}")
            return {
                "status": "failed",
                "chunks": [],
                "error": str(e)
            }
        
    def format_context_string(self, chunks: List[dict]) -> str:
        """Formats RAG chunks into a single text block for the LLM prompt."""
        if not chunks:
            return "No relevant documentation found."
            
        formatted_blocks = []
        for idx, c in enumerate(chunks, 1):
            block = (
                f"Source [{idx}]: {c['filename']} (Title: {c['title']})\n"
                f"Confidence Score: {c['confidence'] * 100:.2f}%\n"
                f"Content:\n{c['content']}\n"
                f"----------------------------------------"
            )
            formatted_blocks.append(block)
        return "\n\n".join(formatted_blocks)
