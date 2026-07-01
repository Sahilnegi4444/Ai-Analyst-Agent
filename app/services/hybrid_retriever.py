import re
import math
import numpy as np
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.models import DocumentChunk
from app.services.embedding import EmbeddingService
from app.config import settings

class SimpleBM25:
    """
    Pure Python, lightweight BM25 implementation for indexing document chunks
    and computing relevance scores for keyword queries.
    """
    def __init__(self, corpus: List[Tuple[int, List[str]]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.avg_doc_len = sum(len(tokens) for _, tokens in corpus) / self.corpus_size if self.corpus_size > 0 else 0
        self.doc_freqs = {}
        self.doc_lens = {}
        self.df = {}
        
        # Calculate term frequencies and document frequencies
        for doc_id, tokens in corpus:
            self.doc_lens[doc_id] = len(tokens)
            freqs = {}
            for t in tokens:
                freqs[t] = freqs.get(t, 0) + 1
            self.doc_freqs[doc_id] = freqs
            for word in freqs:
                self.df[word] = self.df.get(word, 0) + 1
                
        # Calculate IDF values
        self.idf = {}
        for word, freq in self.df.items():
            # BM25 IDF formula
            self.idf[word] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)

    def score(self, query: List[str]) -> List[Tuple[int, float]]:
        scores = []
        for doc_id, freqs in self.doc_freqs.items():
            doc_len = self.doc_lens[doc_id]
            score = 0.0
            for word in query:
                if word in freqs:
                    freq = freqs[word]
                    num = freq * (self.k1 + 1)
                    denom = freq + self.k1 * (1.0 - self.b + self.b * doc_len / self.avg_doc_len)
                    score += self.idf.get(word, 0.0) * (num / denom)
            scores.append((doc_id, score))
        return scores

class HybridRetriever:
    """
    Combines exact keyword code boosting, vector cosine search, BM25 text match,
    RRF rank fusion, and a CrossEncoder deep-learning reranker (Top 20 -> Top 3).
    """
    def __init__(self, db: Session):
        self.db = db
        self.embedding_service = EmbeddingService()
        self.reranker = None
        if settings.ENABLE_RERANKER:
            from app.providers.factory import get_reranker_provider
            self.reranker = get_reranker_provider()
        else:
            print("Reranker is disabled via configuration.")

    def _tokenize(self, text: str) -> List[str]:
        # Regex tokenization
        return re.findall(r'\w+', text.lower())

    def retrieve(self, query: str, top_k: int = 3) -> List[Tuple[DocumentChunk, float]]:
        """
        Executes hybrid search retrieval flow and returns Top K chunks with confidence scores.
        """
        # 1. Fetch all candidate chunks (excluding schemas)
        chunks = self.db.query(DocumentChunk).filter(DocumentChunk.filename != "database_schema.json").all()
        if not chunks:
            return []

        # 2. Check for exact code/identifier matches and filename matches
        patterns = [
            r'\bC\d{4}\b',   # Customer segment codes (C0001 - C5000)
            r'\bP\d{3}\b',   # Product IDs (P001 - P100)
            r'\bS\d{2}\b',   # Supplier IDs (S01 - S10)
            r'\bT\d{5}\b',   # Transaction codes (T00001 - T50000)
            r'\bR\d{5}\b',   # Return records (R00001 - R02000)
            r'\bMC\d{3}\b',  # Campaign IDs (MC001 - MC005)
            r'\bREV\d{5}\b'  # Review IDs
        ]
        exact_matches = set()
        query_upper = query.upper()
        for pattern in patterns:
            found = re.findall(pattern, query_upper)
            for code in found:
                for chunk in chunks:
                    if code in chunk.content.upper():
                        exact_matches.add(chunk)

        # Document filename keyword matches
        filename_matches = set()
        query_lower = query.lower()
        for chunk in chunks:
            fname_lower = chunk.filename.lower()
            if "inventory_sop" in fname_lower:
                if any(re.search(rf"\b{x}\b", query_lower) for x in ["sop", "inventory", "reorder", "stock", "cycle count"]):
                    filename_matches.add(chunk)
            elif "marketing_policy" in fname_lower:
                if any(re.search(rf"\b{x}\b", query_lower) for x in ["marketing", "policy", "campaign", "campain", "discount", "rule", "rules"]):
                    filename_matches.add(chunk)
            elif "supplier_contract" in fname_lower:
                if any(re.search(rf"\b{x}\b", query_lower) for x in ["supplier", "contract", "sla", "deadline", "penalty", "delivery"]):
                    filename_matches.add(chunk)
            elif "warehouse_manual" in fname_lower:
                if any(re.search(rf"\b{x}\b", query_lower) for x in ["warehouse", "manual", "shipping", "handling", "procedures"]):
                    filename_matches.add(chunk)
            elif "executive_report" in fname_lower or "march" in fname_lower:
                if any(re.search(rf"\b{x}\b", query_lower) for x in ["executive", "report", "march", "briefing", "performance"]):
                    filename_matches.add(chunk)

        # 3. BM25 Search
        tokenized_query = self._tokenize(query)
        corpus = [(c.id, self._tokenize(c.content)) for c in chunks]
        bm25 = SimpleBM25(corpus)
        bm25_scores = bm25.score(tokenized_query)
        bm25_scores_dict = {doc_id: score for doc_id, score in bm25_scores}
        bm25_candidates = sorted(chunks, key=lambda x: bm25_scores_dict.get(x.id, 0.0), reverse=True)[:20]

        # 4. Vector Search
        query_vector = self.embedding_service.get_embedding(query)
        vector_results = (
            self.db.query(DocumentChunk, DocumentChunk.embedding.cosine_distance(query_vector).label('distance'))
            .filter(DocumentChunk.filename != "database_schema.json")
            .order_by('distance')
            .limit(20)
            .all()
        )
        vector_candidates = [chunk for chunk, _ in vector_results]

        # 5. Score Fusion via Reciprocal Rank Fusion (RRF)
        rrf_scores = {}
        k = 60
        
        # Rank scores for vector search
        for rank, chunk in enumerate(vector_candidates, 1):
            rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + (1.0 / (k + rank))
            
        # Rank scores for BM25 search
        for rank, chunk in enumerate(bm25_candidates, 1):
            rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + (1.0 / (k + rank))

        # Boost exact keyword matches significantly
        for chunk in exact_matches:
            rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + 1.0

        for chunk in filename_matches:
            rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + 1.5

        # Sort and take Top 20 for reranking
        id_to_chunk = {c.id: c for c in chunks}
        fused_candidates = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:20]
        fused_chunks = [id_to_chunk[chunk_id] for chunk_id, _ in fused_candidates]

        # 6. Reranking using the active provider
        if self.reranker and fused_chunks:
            # Rerank candidates
            doc_contents = [c.content for c in fused_chunks]
            scores = self.reranker.rerank(query, doc_contents)
            
            # Pair candidate chunks with their relevance scores and apply sorting boosts
            chunk_scores = []
            for chunk, score in zip(fused_chunks, scores):
                boosted_score = float(score)
                if chunk in exact_matches:
                    boosted_score += 5.0
                if chunk in filename_matches:
                    boosted_score += 10.0
                chunk_scores.append((chunk, boosted_score, score))
            
            # Sort by boosted score descending
            scored_chunks = sorted(chunk_scores, key=lambda x: x[1], reverse=True)
            top_scored = scored_chunks[:top_k]
            
            # Retrieve final scores (which are already normalized in [0, 1] by the providers)
            results = []
            for chunk, _, score in top_scored:
                confidence = float(score)
                if chunk in exact_matches or chunk in filename_matches:
                    confidence = max(confidence, 0.95)
                results.append((chunk, confidence))
            return results
        else:
            # Fallback to pgvector cosine distance similarity if reranker is disabled
            results = []
            for chunk in fused_chunks[:top_k]:
                vec_chunk = np.array(chunk.embedding)
                vec_query = np.array(query_vector)
                denom = np.linalg.norm(vec_chunk) * np.linalg.norm(vec_query)
                similarity = np.dot(vec_chunk, vec_query) / denom if denom > 0 else 0.0
                confidence = float(round(similarity, 4))
                if chunk in exact_matches or chunk in filename_matches:
                    confidence = max(confidence, 0.95)
                results.append((chunk, confidence))
            return results
