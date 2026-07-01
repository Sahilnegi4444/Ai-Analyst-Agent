from abc import ABC, abstractmethod
from typing import List

class EmbeddingProvider(ABC):
    """Abstract base class for text embedding providers."""
    
    @abstractmethod
    def embed(self, text: str, task: str = "retrieval.query") -> List[float]:
        """Generate a vector embedding for a single text chunk."""
        pass
        
    @abstractmethod
    def embed_batch(self, texts: List[str], task: str = "retrieval.passage") -> List[List[float]]:
        """Generate vector embeddings for a batch of text chunks."""
        pass

class RerankerProvider(ABC):
    """Abstract base class for document reranking providers."""
    
    @abstractmethod
    def rerank(self, query: str, documents: List[str]) -> List[float]:
        """
        Reranks a list of documents against a query.
        Returns a list of relevance scores (floats in [0, 1]) matching the document list size.
        """
        pass
