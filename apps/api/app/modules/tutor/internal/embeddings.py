import hashlib
import math
from typing import Protocol

import httpx

from app.shared.config import get_settings


class EmbeddingsProvider(Protocol):
    async def embed_query(self, text: str) -> list[float]: ...

    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...


class GeminiEmbeddings:
    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "text-embedding-004",
        dimension: int = 768,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or getattr(settings, "google_api_key", None) or ""
        self.model_name = model_name
        self.dimension = dimension
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def embed_query(self, text: str) -> list[float]:
        if not self.api_key:
            # Fallback to deterministic pseudo-vector if no API key configured in dev
            return MockEmbeddings()._generate_vector(text, self.dimension)

        url = f"{self.base_url}/models/{self.model_name}:embedContent?key={self.api_key}"
        payload = {
            "model": f"models/{self.model_name}",
            "content": {"parts": [{"text": text}]},
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(url, json=payload)
            if res.status_code != 200:
                # Log or fall back safely
                return MockEmbeddings()._generate_vector(text, self.dimension)
            data = res.json()
            return list(data["embedding"]["values"])

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        if not self.api_key:
            mock = MockEmbeddings(dimension=self.dimension)
            return [mock._generate_vector(t, self.dimension) for t in texts]

        # Batch embed up to 100 texts at a time
        url = f"{self.base_url}/models/{self.model_name}:batchEmbedContents?key={self.api_key}"
        requests = [
            {
                "model": f"models/{self.model_name}",
                "content": {"parts": [{"text": t}]},
            }
            for t in texts
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, json={"requests": requests})
            if res.status_code != 200:
                mock = MockEmbeddings(dimension=self.dimension)
                return [mock._generate_vector(t, self.dimension) for t in texts]
            data = res.json()
            return [list(item["values"]) for item in data.get("embeddings", [])]


STOPWORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "what",
    "how",
    "why",
    "of",
    "and",
    "or",
    "in",
    "on",
    "to",
    "for",
    "with",
    "about",
    "tell",
    "me",
    "can",
    "you",
    "explain",
    "this",
    "that",
    "it",
    "from",
    "at",
    "does",
    "did",
    "who",
    "when",
    "where",
    "under",
    "between",
    "should",
    "i",
    "be",
}


class MockEmbeddings:
    """Deterministic, normalized word-token embedding generator for testing."""

    def __init__(self, dimension: int = 768) -> None:
        self.dimension = dimension

    def _generate_vector(self, text: str, dim: int) -> list[float]:
        import re

        clean = text.lower().strip()
        all_words = re.findall(r"\w+", clean)
        meaningful = [w for w in all_words if w not in STOPWORDS]
        words = meaningful if meaningful else all_words
        if not words:
            vec = [0.0] * dim
            vec[0] = 1.0
            return vec

        vec = [0.0] * dim
        for w in words:
            # Deterministic pseudo-orthogonal word embedding
            idx1 = int(hashlib.sha256(f"{w}_a".encode()).hexdigest()[:8], 16) % dim
            idx2 = int(hashlib.sha256(f"{w}_b".encode()).hexdigest()[:8], 16) % dim
            idx3 = int(hashlib.sha256(f"{w}_c".encode()).hexdigest()[:8], 16) % dim
            vec[idx1] += 1.0
            vec[idx2] += 0.5
            vec[idx3] -= 0.5

        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    async def embed_query(self, text: str) -> list[float]:
        return self._generate_vector(text, self.dimension)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._generate_vector(t, self.dimension) for t in texts]
