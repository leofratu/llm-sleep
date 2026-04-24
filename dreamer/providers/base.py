"""Abstract provider interface.

Every provider returns a plain `CompletionResult` so the rest of the
codebase is provider-agnostic. The emulator only ever asks for:
    provider.complete(system, messages, temperature, top_p, max_tokens)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class Message:
    role: str  # "user" | "assistant"
    content: str


@dataclass
class CompletionResult:
    text: str
    model: str
    provider: str
    usage: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


class DreamProvider(Protocol):
    name: str

    async def complete(
        self,
        *,
        model: str,
        system: str,
        messages: list[Message],
        temperature: float,
        top_p: float,
        max_tokens: int,
    ) -> CompletionResult: ...
