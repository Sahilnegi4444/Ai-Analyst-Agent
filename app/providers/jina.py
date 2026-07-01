import requests
from typing import List
from app.providers.base import EmbeddingProvider, RerankerProvider
from app.config import settings

class JinaEmbeddingProvider(EmbeddingProvider):
    """Jina AI cloud embeddings provider."""
    
    def __init__(self):
        self.api_key = settings.JINA_API_KEY
        self.url = "https://api.jina.ai/v1/embeddings"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def embed(self, text: str, task: str = "retrieval.query") -> List[float]:
        if not self.api_key:
            raise ValueError("JINA_API_KEY environment variable is not configured.")
            
        payload = {
            "model": "jina-embeddings-v3",
            "input": [text],
            "dimensions": 384,
            "task": task
        }
        
        response = requests.post(self.url, headers=self.headers, json=payload, timeout=15)
        response.raise_for_status()
        
        data = response.json().get("data", [])
        if not data:
            raise RuntimeError("Jina Embeddings API returned an empty response.")
        return data[0]["embedding"]

    def embed_batch(self, texts: List[str], task: str = "retrieval.passage") -> List[List[float]]:
        if not self.api_key:
            raise ValueError("JINA_API_KEY environment variable is not configured.")
        if not texts:
            return []
            
        payload = {
            "model": "jina-embeddings-v3",
            "input": texts,
            "dimensions": 384,
            "task": task
        }
        
        response = requests.post(self.url, headers=self.headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json().get("data", [])
        # Jina returns list of objects containing embedding
        embeddings = [item["embedding"] for item in data]
        return embeddings

class JinaRerankerProvider(RerankerProvider):
    """Jina AI cloud reranking provider."""
    
    def __init__(self):
        self.api_key = settings.JINA_API_KEY
        self.url = "https://api.jina.ai/v1/rerank"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def rerank(self, query: str, documents: List[str]) -> List[float]:
        if not self.api_key:
            raise ValueError("JINA_API_KEY environment variable is not configured.")
        if not documents:
            return []
            
        payload = {
            "model": "jina-reranker-v2-base-multilingual",
            "query": query,
            "documents": documents
        }
        
        response = requests.post(self.url, headers=self.headers, json=payload, timeout=20)
        response.raise_for_status()
        
        results = response.json().get("results", [])
        
        # Jina returns results sorted by score; map them back to the original index sequence
        scores = [0.0] * len(documents)
        for res in results:
            idx = res["index"]
            score = res["relevance_score"]
            scores[idx] = score
            
        return scores
