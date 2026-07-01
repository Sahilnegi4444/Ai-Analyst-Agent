from groq import Groq
from typing import List, Dict, Any
from app.config import settings
from app.providers.base import LLMProvider, LLMResponse

class GroqLLMProvider(LLMProvider):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(GroqLLMProvider, cls).__new__(cls, *args, **kwargs)
            cls._instance._init_client()
        return cls._instance

    def _init_client(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        model = kwargs.pop("model", settings.GROQ_GENERATOR_MODEL)
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )
        content = response.choices[0].message.content
        prompt_tokens = getattr(response.usage, "prompt_tokens", 0)
        completion_tokens = getattr(response.usage, "completion_tokens", 0)
        return LLMResponse(content, prompt_tokens, completion_tokens)
