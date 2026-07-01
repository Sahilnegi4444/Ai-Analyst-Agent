import gc
from typing import List
from app.providers.base import EmbeddingProvider, RerankerProvider
from app.config import settings

class LocalEmbeddingProvider(EmbeddingProvider):
    """Local offline embeddings provider using SentenceTransformers."""
    
    def __init__(self):
        self.model = None
        
    def _init_model(self):
        if self.model is not None:
            return
        try:
            import torch
            from sentence_transformers import SentenceTransformer
            
            # Restrict thread count and turn off gradients to optimize memory
            torch.set_num_threads(1)
            torch.set_grad_enabled(False)
            
            print(f"Loading local embedding model: {settings.EMBEDDING_MODEL_NAME}...")
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME, device="cpu")
            gc.collect()
            print("Local embedding model loaded successfully.")
        except ModuleNotFoundError:
            raise ImportError(
                "Local inference dependencies ('sentence-transformers' and 'torch') are not installed. "
                "Please install them using: pip install -r requirements-dev.txt"
            )
            
    def embed(self, text: str, task: str = "retrieval.query") -> List[float]:
        self._init_model()
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
        
    def embed_batch(self, texts: List[str], task: str = "retrieval.passage") -> List[List[float]]:
        self._init_model()
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

class LocalRerankerProvider(RerankerProvider):
    """Local offline reranking provider using CrossEncoder."""
    
    def __init__(self):
        self.model = None
        
    def _init_model(self):
        if self.model is not None:
            return
        try:
            import torch
            from sentence_transformers import CrossEncoder
            
            torch.set_num_threads(1)
            torch.set_grad_enabled(False)
            
            print(f"Loading local CrossEncoder model: {settings.RERANK_MODEL_NAME}...")
            self.model = CrossEncoder(settings.RERANK_MODEL_NAME)
            gc.collect()
            print("Local CrossEncoder model loaded successfully.")
        except ModuleNotFoundError:
            raise ImportError(
                "Local inference dependencies ('sentence-transformers' and 'torch') are not installed. "
                "Please install them using: pip install -r requirements-dev.txt"
            )
            
    def rerank(self, query: str, documents: List[str]) -> List[float]:
        if not documents:
            return []
        self._init_model()
        
        pairs = [[query, doc] for doc in documents]
        scores = self.model.predict(pairs)
        
        # Map class entailment logit (class 1 for ettin-reranker) to [0, 1] range via sigmoid
        import numpy as np
        final_scores = []
        for score in scores:
            entailment_logit = float(score[1])
            confidence = float(1.0 / (1.0 + np.exp(-entailment_logit)))
            final_scores.append(confidence)
            
        return final_scores
