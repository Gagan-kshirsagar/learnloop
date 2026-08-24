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
        self._mock_embeddings = MockEmbeddings()
        self._mock_llm = MockLLM()

    def get_embeddings_provider(self) -> EmbeddingsProvider:
        provider_name = getattr(self.settings, "embeddings_provider", "gemini").lower()
        api_key = getattr(self.settings, "google_api_key", None)
        if provider_name == "mock" or not api_key:
            return self._mock_embeddings
        return GeminiEmbeddings(api_key=api_key)

    def get_llm_provider(self) -> LLMProvider:
        provider_name = getattr(self.settings, "llm_provider", "gemini").lower()
        api_key = getattr(self.settings, "google_api_key", None)
        if provider_name == "mock" or not api_key:
            return self._mock_llm
        return GeminiLLM(api_key=api_key)


_router_instance: ModelRouter | None = None


def get_model_router() -> ModelRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = ModelRouter()
    return _router_instance
