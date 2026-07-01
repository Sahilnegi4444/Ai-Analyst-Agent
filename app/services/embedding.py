from typing import List
from app.providers.factory import get_embedding_provider

class EmbeddingService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        # Implement singleton pattern to wrap active provider
        if not cls._instance:
            cls._instance = super(EmbeddingService, cls).__new__(cls, *args, **kwargs)
            cls._instance._init_provider()
        return cls._instance

    def _init_provider(self):
        self.provider = get_embedding_provider()

    def get_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for a single text chunk."""
        return self.provider.embed(text, task="retrieval.query")

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a batch of text chunks."""
        return self.provider.embed_batch(texts, task="retrieval.document")
