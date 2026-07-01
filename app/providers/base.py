from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LLMResponse:
    def __init__(self, content: str, prompt_tokens: int = 0, completion_tokens: int = 0):
        self.content = content
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        
        class Usage:
            def __init__(self, p, c):
                self.prompt_tokens = p
                self.completion_tokens = c
        self.usage = Usage(prompt_tokens, completion_tokens)
        
        class Choice:
            class Message:
                def __init__(self, content):
                    self.content = content
            def __init__(self, content):
                self.message = Choice.Message(content)
        self.choices = [Choice(content)]

class EmbeddingProvider(ABC):
    @abstractmethod
    def get_embedding(self, text: str) -> List[float]:
        """Generate vector embedding for a single text chunk."""
        pass

    @abstractmethod
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a batch of text chunks."""
        pass

class RerankerProvider(ABC):
    @abstractmethod
    def predict(self, query: str, documents: List[str]) -> List[float]:
        """
        Compute similarity scores between the query and multiple documents.
        Returns a list of relevance scores (higher = more relevant).
        """
        pass

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """
        Generate chat completion response from structured messages.
        """
        pass
