"""Shared OpenAI-compatible Chat Completions client.

Used by the OpenAI, Google (OpenAI-compat), and Custom providers so we
don't duplicate HTTP plumbing three times.
"""

from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from .base import CompletionResult, Message


async def chat_complete_openai_style(
    *,
    provider_name: str,
    api_key: str,
    base_url: str,
    model: str,
    system: str,
    messages: list[Message],
    temperature: float,
    top_p: float,
    max_tokens: int,
) -> CompletionResult:
    msgs = [{"role": "system", "content": system}]
    msgs += [{"role": m.role, "content": m.content} for m in messages]

    payload = {
        "model": model,
        "messages": msgs,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _call() -> dict:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                f"{base_url.rstrip('/')}/chat/completions",
                json=payload,
                headers=headers,
            )
            if r.status_code >= 400:
                raise RuntimeError(
                    f"{provider_name} {r.status_code}: {r.text[:600]}"
                )
            return r.json()

    data = await _call()
    text = data["choices"][0]["message"].get("content") or ""
    return CompletionResult(
        text=text,
        model=model,
        provider=provider_name,
        usage=data.get("usage", {}),
        raw=data,
    )
