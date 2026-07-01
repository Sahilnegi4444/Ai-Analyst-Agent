from sentence_transformers import CrossEncoder
import numpy as np
from typing import List
from app.config import settings
from app.providers.base import RerankerProvider

class LocalRerankerProvider(RerankerProvider):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LocalRerankerProvider, cls).__new__(cls, *args, **kwargs)
            cls._instance._init_model()
        return cls._instance

    def _init_model(self):
        self.model = None
        if settings.ENABLE_RERANKER:
            try:
                print(f"Loading reranker model: {settings.RERANK_MODEL_NAME}...")
                self.model = CrossEncoder(settings.RERANK_MODEL_NAME)
                print("Reranker model loaded successfully.")
            except Exception as e:
                print(f"[WARNING] Failed to load reranker model offline: {e}. Running without reranking.")
        else:
            print("Reranker is disabled by configuration (ENABLE_RERANKER=false). Skipping model load to save RAM.")

    def predict(self, query: str, documents: List[str]) -> List[float]:
        if not self.model or not documents:
            return []
            
        pairs = [[query, doc] for doc in documents]
        scores = self.model.predict(pairs)
        
        formatted_scores = []
        for score in scores:
            if hasattr(score, "__len__") and len(score) > 1:
                formatted_scores.append(float(score[1]))
            else:
                formatted_scores.append(float(score))
        return formatted_scores
