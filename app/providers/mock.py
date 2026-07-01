from typing import List
from app.providers.base import EmbeddingProvider, RerankerProvider

class MockEmbeddingProvider(EmbeddingProvider):
    """Mock offline embedding provider for unit tests and local sandboxes."""
    
    def embed(self, text: str, task: str = "retrieval.query") -> List[float]:
        # Return a deterministic 384-dimensional vector based on input content
        # Use simple hashing or padding to maintain size consistency
        val = (hash(text) % 1000) / 1000.0
        return [val] * 384
        
    def embed_batch(self, texts: List[str], task: str = "retrieval.passage") -> List[List[float]]:
        return [self.embed(t, task) for t in texts]

class MockRerankerProvider(RerankerProvider):
    """Mock offline reranking provider for unit tests and local sandboxes."""
    
    def rerank(self, query: str, documents: List[str]) -> List[float]:
        # Return a mock confidence sequence, e.g. descending scores from 0.9 down to 0.1
        if not documents:
            return []
        n = len(documents)
        return [max(0.0, min(1.0, 0.9 - (i * 0.1))) for i in range(n)]
