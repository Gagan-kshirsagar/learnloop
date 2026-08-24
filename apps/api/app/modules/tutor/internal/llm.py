import asyncio
import json
from collections.abc import AsyncIterator
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

    def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
    ) -> AsyncIterator[str]: ...


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

    def _build_payload(
        self,
        prompt: str,
        system_instruction: str | None,
        temperature: float,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 1024,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        return payload

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        if not self.api_key:
            return MockLLM()._generate_grounded_mock(prompt)

        url = f"{self.base_url}/models/{self.model_name}:generateContent?key={self.api_key}"
        payload = self._build_payload(prompt, system_instruction, temperature)

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

    async def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
    ) -> AsyncIterator[str]:
        if not self.api_key:
            async for token in MockLLM().generate_stream(prompt, system_instruction, temperature):
                yield token
            return

        url = (
            f"{self.base_url}/models/{self.model_name}:streamGenerateContent"
            f"?alt=sse&key={self.api_key}"
        )
        payload = self._build_payload(prompt, system_instruction, temperature)

        async with (
            httpx.AsyncClient(timeout=45.0) as client,
            client.stream("POST", url, json=payload) as response,
        ):
            if response.status_code != 200:
                async for token in MockLLM().generate_stream(prompt):
                    yield token
                return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        raw_data = line[6:].strip()
                        if not raw_data or raw_data == "[DONE]":
                            continue
                        try:
                            chunk = json.loads(raw_data)
                            candidates = chunk.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for p in parts:
                                    text = p.get("text", "")
                                    if text:
                                        yield text
                        except Exception:
                            continue


class MockLLM:
    """Deterministic mock LLM that generates grounded answers quoting the prompt context."""

    def _generate_grounded_mock(self, prompt: str) -> str:
        if "Lesson Context Chunks:" in prompt:
            ctx_part = (
                prompt.split("Lesson Context Chunks:")[1]
                .split("Student Question:")[0]
                .split("Current Question:")[0]
                .strip()
            )
            lines = [
                ln.strip()
                for ln in ctx_part.splitlines()
                if ln.strip() and not ln.startswith("[")
            ]
            excerpt = "\n".join(lines[:4]) if lines else "the curriculum material"
            return (
                f"**Based on the lesson material:**\n\n"
                f"{excerpt}\n\n"
                f"*This explains the core concept as described in the curriculum.*"
            )
        return "That isn't covered in this lesson."

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,  # noqa: ARG002
        temperature: float = 0.2,  # noqa: ARG002
    ) -> str:
        return self._generate_grounded_mock(prompt)

    async def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,  # noqa: ARG002
        temperature: float = 0.2,  # noqa: ARG002
    ) -> AsyncIterator[str]:
        full_text = self._generate_grounded_mock(prompt)
        words = full_text.split(" ")
        for i, word in enumerate(words):
            token = word if i == len(words) - 1 else word + " "
            yield token
            # Micro yield delay for realistic async streaming simulation
            await asyncio.sleep(0.01)
