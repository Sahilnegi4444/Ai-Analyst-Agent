from sentence_transformers import SentenceTransformer
from typing import List
from app.config import settings
from app.providers.base import EmbeddingProvider

class LocalEmbeddingProvider(EmbeddingProvider):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LocalEmbeddingProvider, cls).__new__(cls, *args, **kwargs)
            cls._instance._init_model()
        return cls._instance

    def _init_model(self):
        print(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}...")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        print("Embedding model loaded successfully.")

    def get_embedding(self, text: str) -> List[float]:
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()
