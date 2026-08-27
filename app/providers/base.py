from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Abstract base class for text embedding providers."""

    @abstractmethod
    def embed(self, text: str, task: str = "retrieval.query") -> list[float]:
        """Generate a vector embedding for a single text chunk."""

    @abstractmethod
    def embed_batch(self, texts: list[str], task: str = "retrieval.passage") -> list[list[float]]:
        """Generate vector embeddings for a batch of text chunks."""

class RerankerProvider(ABC):
    """Abstract base class for document reranking providers."""

    @abstractmethod
    def rerank(self, query: str, documents: list[str]) -> list[float]:
        """
        Reranks a list of documents against a query.
        Returns a list of relevance scores (floats in [0, 1]) matching the document list size.
        """
