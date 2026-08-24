import json
from collections.abc import AsyncIterator
from typing import Protocol

import httpx

from app.shared.config import get_settings


class LLMProvider(Protocol):
    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        """Generate a grounded completion for the given prompt."""
        ...

    def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
    ) -> AsyncIterator[str]:
        """Stream a grounded completion token-by-token."""
        ...


class GeminiLLM:
    """Google Gemini LLM provider calling gemini-1.5-flash."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-1.5-flash",
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or getattr(settings, "google_api_key", None)
        self.model = model
        self.endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        )
        self.stream_endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
            f":streamGenerateContent?alt=sse"
        )

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        payload: dict[str, object] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature},
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                self.endpoint,
                params={"key": self.api_key},
                json=payload,
            )
            if res.status_code != 200:
                raise RuntimeError(f"Gemini LLM error {res.status_code}: {res.text}")
            data = res.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return "That isn't covered in this lesson."
            parts = candidates[0].get("content", {}).get("parts", [])
            return "".join(p.get("text", "") for p in parts)

    async def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
    ) -> AsyncIterator[str]:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        payload: dict[str, object] = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature},
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        async with (
            httpx.AsyncClient(timeout=60.0) as client,
            client.stream(
                "POST",
                self.stream_endpoint,
                params={"key": self.api_key},
                json=payload,
            ) as response,
        ):
            if response.status_code != 200:
                err_body = await response.aread()
                raise RuntimeError(
                    f"Gemini streaming error {response.status_code}: {err_body.decode()}"
                )

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:].strip()
                    if not data_str or data_str == "[DONE]":
                        continue
                    try:
                        chunk = json.loads(data_str)
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
        prompt_lower = prompt.lower()
        if "Observed Evidence from Tools:" in prompt or "Guidance Instructions:" in prompt:
            is_slice_topic = "slice" in prompt_lower or "palindrome" in prompt_lower

            if "Escalation Mode: REVEAL_ALLOWED" in prompt:
                if is_slice_topic:
                    return (
                        "**Worked Solution Breakdown:**\n\n"
                        "Here is the complete solution using Python's extended slice syntax:\n\n"
                        "```python\n"
                        "def is_palindrome(s: str) -> bool:\n"
                        "    # Normalize and compare string with its reverse\n"
                        "    clean = s.lower().replace(' ', '')\n"
                        "    return clean == clean[::-1]\n"
                        "```\n\n"
                        "**Explanation:**\n"
                        "1. `s[::-1]` uses slice notation `[start:stop:step]` with a `-1` step "
                        "to reverse the sequence in $O(N)$ time.\n"
                        "2. Direct equality comparison `==` evaluates whether forward and reversed "
                        "strings match.\n\n"
                        "*This worked explanation is provided after verified attempts.*"
                    )
                return (
                    "**Worked Solution Breakdown:**\n\n"
                    "Here is the step-by-step conceptual walkthrough to resolve the issue:\n"
                    "1. Ensure your return statement is inside the correct conditional block.\n"
                    "2. Check that variable types match the expected function signature.\n\n"
                    "*This worked explanation is provided after verified attempts.*"
                )

            if "Escalation Mode: SPECIFIC_HINT" in prompt:
                if is_slice_topic:
                    return (
                        "**Specific Diagnostic Hint:** Based on the lesson material on "
                        "String Slicing, recall that Python's extended slice syntax "
                        "`[start:stop:step]` allows negative stepping. "
                        "Specifically, `s[::-1]` reverses a string.\n\n"
                        "*Examine whether your function compares the string "
                        "directly with its reversed slice `[::-1]`.*"
                    )
                return (
                    "**Specific Diagnostic Hint:** Based on the lesson material, "
                    "examine the specific return statement and conditional branches in your code. "
                    "Ensure that edge case inputs return the expected boolean result.\n\n"
                    "*Check the lesson notes for syntax and return value examples.*"
                )

            # Default / CONCEPTUAL_NUDGE
            if is_slice_topic:
                return (
                    "**Socratic Hint:** Based on the lesson material, "
                    "think about the definition of a palindrome—a sequence that reads the same "
                    "forwards and backwards. How can Python's slicing notation help you obtain "
                    "a reversed copy of the string to compare against?\n\n"
                    "*Reflect on the slice syntax `[start:stop:step]` covered in this lesson.*"
                )
            return (
                "**Socratic Hint:** Based on the lesson material, "
                "take a close look at how your logic handles the return value. "
                "What happens when the condition is evaluated on the edge cases?\n\n"
                "*Reflect on the core concepts in the lesson material to guide your fix.*"
            )

        if "Lesson Context Chunks:" in prompt:
            ctx_part = (
                prompt.split("Lesson Context Chunks:")[1]
                .split("Student Question:")[0]
                .split("Current Question:")[0]
                .strip()
            )
            lines = [
                ln.strip() for ln in ctx_part.splitlines() if ln.strip() and not ln.startswith("[")
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
