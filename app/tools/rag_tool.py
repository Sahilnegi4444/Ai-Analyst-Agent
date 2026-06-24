from sqlalchemy.orm import Session
from app.repositories import DocumentRepository
from app.services.embedding import EmbeddingService
from app.services.hybrid_retriever import HybridRetriever
from app.services.context_compressor import ContextCompressor
from app.services.cache_service import RedisCacheService
from typing import List, Dict, Any

class RAGTool:
    """
    Optimized RAG tool that uses hybrid search retrieval (vector + BM25 + exact boosts),
    reranking via a CrossEncoder, and Llama-3.1-8b based chunk context compression.
    """
    def __init__(self, db: Session):
        self.db = db
        self.doc_repository = DocumentRepository(db)
        self.embedding_service = EmbeddingService()

    def retrieve_context(self, query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Retrieves context using hybrid search, reranking, and compression.
        Utilizes Redis to cache retrieved and compressed text.
        """
        try:
            cache_service = RedisCacheService()
            
            # 1. Try to fetch from retrieval cache
            cached_results = cache_service.get_cached_retrieval(query)
            if cached_results is not None:
                return {
                    "status": "success",
                    "chunks": cached_results,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "error": None
                }

            # 2. Cache Miss: Execute hybrid search & reranking
            retriever = HybridRetriever(self.db)
            similar_chunks = retriever.retrieve(query, top_k=top_k)

            # 3. Dynamic context compression with Llama model
            compressor = ContextCompressor()
            results = []
            
            total_prompt_tokens = 0
            total_completion_tokens = 0

            for chunk, confidence in similar_chunks:
                # Check cache for this specific compressed chunk
                cached_comp = cache_service.get_cached_compressed(query, chunk.id)
                if cached_comp:
                    compressed_text = cached_comp
                else:
                    # Compress chunk content
                    comp_res = compressor.compress_chunk(query, chunk.content)
                    compressed_text = comp_res["compressed_text"]
                    total_prompt_tokens += comp_res.get("prompt_tokens", 0)
                    total_completion_tokens += comp_res.get("completion_tokens", 0)
                    
                    # Cache compressed content
                    cache_service.set_cached_compressed(query, chunk.id, compressed_text)

                results.append({
                    "filename": chunk.filename,
                    "title": chunk.title,
                    "content": compressed_text,
                    "raw_content": chunk.content,
                    "confidence": confidence
                })

            # 4. Cache full RAG results
            cache_service.set_cached_retrieval(query, results)

            return {
                "status": "success",
                "chunks": results,
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "error": None
            }
        except Exception as e:
            print(f"[ERROR] Optimized RAG Retrieval failure: {e}")
            return {
                "status": "failed",
                "chunks": [],
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "error": str(e)
            }
        
    def format_context_string(self, chunks: List[dict]) -> str:
        """Formats compressed RAG chunks into a single text block for the LLM prompt."""
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

