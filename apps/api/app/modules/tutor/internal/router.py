from app.modules.tutor.internal.embeddings import (
    EmbeddingsProvider,
    GeminiEmbeddings,
    MockEmbeddings,
)
from app.modules.tutor.internal.llm import GeminiLLM, LLMProvider, MockLLM
from app.shared.config import get_settings


class ModelRouter:
    def __init__(self) -> None:
        self.settings = get_settings()

    def get_embeddings_provider(self) -> EmbeddingsProvider:
        provider_name = getattr(self.settings, "embeddings_provider", "gemini").lower()
        if provider_name == "mock":
            return MockEmbeddings()
        return GeminiEmbeddings()

    def get_llm_provider(self) -> LLMProvider:
        provider_name = getattr(self.settings, "llm_provider", "gemini").lower()
        if provider_name == "mock":
            return MockLLM()
        return GeminiLLM()


_router_instance: ModelRouter | None = None


def get_model_router() -> ModelRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = ModelRouter()
    return _router_instance
