from typing import Any, Protocol

import httpx

from app.shared.config import get_settings


class LLMProvider(Protocol):
    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
    ) -> str: ...


class GeminiLLM:
    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gemini-1.5-flash",
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or getattr(settings, "google_api_key", None) or ""
        self.model_name = model_name
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        if not self.api_key:
            return MockLLM()._generate_grounded_mock(prompt)

        url = f"{self.base_url}/models/{self.model_name}:generateContent?key={self.api_key}"
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 1024,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(url, json=payload)
            if res.status_code != 200:
                return MockLLM()._generate_grounded_mock(prompt)
            data = res.json()
            try:
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return str(parts[0].get("text", ""))
            except Exception:
                pass
            return MockLLM()._generate_grounded_mock(prompt)


class MockLLM:
    """Deterministic mock LLM that generates grounded answers quoting the prompt context."""

    def _generate_grounded_mock(self, prompt: str) -> str:
        if "Lesson Context Chunks:" in prompt:
            ctx_part = (
                prompt.split("Lesson Context Chunks:")[1].split("Student Question:")[0].strip()
            )
            lines = [
                ln.strip() for ln in ctx_part.splitlines() if ln.strip() and not ln.startswith("[")
            ]
            snippet = lines[0] if lines else "the curriculum material"
            return (
                f"Based on the lesson material: {snippet}\n\n"
                "This explains the core concept as described in the curriculum."
            )
        return "That isn't covered in this lesson."

    async def generate(
        self,
        prompt: str,
        _system_instruction: str | None = None,
        _temperature: float = 0.2,
    ) -> str:
        return self._generate_grounded_mock(prompt)
