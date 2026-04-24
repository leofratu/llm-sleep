"""Google Gemini provider — uses the OpenAI-compatible endpoint.

See: https://ai.google.dev/gemini-api/docs/openai
Base URL: https://generativelanguage.googleapis.com/v1beta/openai
The API key is sent as an `Authorization: Bearer ...` header.
"""

from __future__ import annotations

from ._openai_http import chat_complete_openai_style
from .base import CompletionResult, Message


class GoogleProvider:
    name = "google"

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url

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
        return await chat_complete_openai_style(
            provider_name=self.name,
            api_key=self.api_key,
            base_url=self.base_url,
            model=model,
            system=system,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )
