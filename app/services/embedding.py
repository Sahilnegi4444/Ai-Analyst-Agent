from typing import List
from app.providers.embedding import LocalEmbeddingProvider

class EmbeddingService:
    def __init__(self):
        self.provider = LocalEmbeddingProvider()

    def get_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for a single text chunk using the provider."""
        return self.provider.get_embedding(text)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a batch of text chunks using the provider."""
        return self.provider.get_embeddings(texts)
