from app.providers.base import EmbeddingProvider, RerankerProvider
from app.config import settings

# Global cached singletons to prevent multiple initializations
_embedding_provider_instance = None
_reranker_provider_instance = None

def get_embedding_provider() -> EmbeddingProvider:
    """Returns the singleton instance of the configured EmbeddingProvider."""
    global _embedding_provider_instance
    if _embedding_provider_instance is None:
        provider_name = getattr(settings, "EMBEDDING_PROVIDER", "jina").lower()
        
        if provider_name == "jina":
            from app.providers.jina import JinaEmbeddingProvider
            _embedding_provider_instance = JinaEmbeddingProvider()
        elif provider_name == "local":
            from app.providers.local import LocalEmbeddingProvider
            _embedding_provider_instance = LocalEmbeddingProvider()
        elif provider_name == "mock":
            from app.providers.mock import MockEmbeddingProvider
            _embedding_provider_instance = MockEmbeddingProvider()
        else:
            raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {provider_name}")
            
    return _embedding_provider_instance

def get_reranker_provider() -> RerankerProvider:
    """Returns the singleton instance of the configured RerankerProvider."""
    global _reranker_provider_instance
    if _reranker_provider_instance is None:
        provider_name = getattr(settings, "RERANKER_PROVIDER", "jina").lower()
        
        if provider_name == "jina":
            from app.providers.jina import JinaRerankerProvider
            _reranker_provider_instance = JinaRerankerProvider()
        elif provider_name == "local":
            from app.providers.local import LocalRerankerProvider
            _reranker_provider_instance = LocalRerankerProvider()
        elif provider_name == "mock":
            from app.providers.mock import MockRerankerProvider
            _reranker_provider_instance = MockRerankerProvider()
        else:
            raise ValueError(f"Unsupported RERANKER_PROVIDER: {provider_name}")
            
    return _reranker_provider_instance
