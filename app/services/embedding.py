from sentence_transformers import SentenceTransformer
from typing import List
from app.config import settings

class EmbeddingService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        # Implement singleton pattern to avoid reloading model multiple times
        if not cls._instance:
            cls._instance = super(EmbeddingService, cls).__new__(cls, *args, **kwargs)
            cls._instance._init_model()
        return cls._instance

    def _init_model(self):
        print(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}...")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        print("Embedding model loaded successfully.")

    def get_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for a single text chunk."""
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a batch of text chunks."""
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()
