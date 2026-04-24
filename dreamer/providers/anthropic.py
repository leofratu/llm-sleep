"""Anthropic Messages API provider.

Also works against any Anthropic-compatible endpoint (ex: OpenRouter's
`/v1/messages` proxy or Z.ai) — just override `ANTHROPIC_BASE_URL`.
"""

from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import CompletionResult, Message


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    async def complete(
        self,
        *,
        model: str,
        system: str,
        messages: list[Message],
        temperature: float,
        top_p: float,
        max_tokens: int,
    ) -> CompletionResult:
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "temperature": min(temperature, 1.0),  # Anthropic caps at 1.0
            "top_p": top_p,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
        async def _call() -> dict:
            async with httpx.AsyncClient(timeout=120.0) as client:
                r = await client.post(
                    f"{self.base_url}/v1/messages",
                    json=payload,
                    headers=headers,
                )
                if r.status_code >= 400:
                    raise RuntimeError(
                        f"Anthropic {r.status_code}: {r.text[:600]}"
                    )
                return r.json()

        data = await _call()

        # Concatenate all text blocks in the response.
        text = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )
        return CompletionResult(
            text=text,
            model=model,
            provider=self.name,
            usage=data.get("usage", {}),
            raw=data,
        )
