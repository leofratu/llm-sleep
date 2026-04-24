"""Provider registry — turns `provider` string from config into a client."""

from __future__ import annotations

from typing import Dict

from ..config import Config, env
from .base import DreamProvider
from .anthropic import AnthropicProvider
from .google import GoogleProvider
from .openai import OpenAIProvider
from .custom import CustomOpenAICompatibleProvider


def build_providers(cfg: Config) -> Dict[str, DreamProvider]:
    providers: Dict[str, DreamProvider] = {}

    if env("ANTHROPIC_API_KEY"):
        providers["anthropic"] = AnthropicProvider(
            api_key=env("ANTHROPIC_API_KEY"),
            base_url=env("ANTHROPIC_BASE_URL") or "https://api.anthropic.com",
        )

    if env("GEMINI_API_KEY"):
        providers["google"] = GoogleProvider(
            api_key=env("GEMINI_API_KEY"),
            # Use Google's OpenAI-compatible endpoint so the client stays simple.
            base_url=env("GOOGLE_OPENAI_BASE_URL")
            or "https://generativelanguage.googleapis.com/v1beta/openai",
        )

    if env("OPENAI_API_KEY"):
        providers["openai"] = OpenAIProvider(
            api_key=env("OPENAI_API_KEY"),
            base_url=env("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        )

    if env("CUSTOM_BASE_URL") and env("CUSTOM_API_KEY"):
        providers["custom"] = CustomOpenAICompatibleProvider(
            api_key=env("CUSTOM_API_KEY"),
            base_url=env("CUSTOM_BASE_URL"),
        )

    if not providers:
        raise RuntimeError(
            "No providers configured. Set at least one of "
            "ANTHROPIC_API_KEY / GEMINI_API_KEY / OPENAI_API_KEY / CUSTOM_*."
        )
    return providers


__all__ = ["build_providers", "DreamProvider"]
