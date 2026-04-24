"""Single entrypoint to run any sleep stage.

Each stage is a (system prompt, user prompt template, config) triple, and
every stage is invoked through `run_stage` which handles provider routing
and records the result into memory as a DreamRecord.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..config import Config
from ..memory.store import DreamRecord, MemoryStore
from ..providers import DreamProvider
from ..providers.base import Message
from .prompts import STAGE_PROMPTS


@dataclass
class StageOutput:
    stage: str
    text: str
    provider: str
    model: str
    seed_ids: list[str]


async def run_stage(
    *,
    stage: str,
    cycle: int,
    cfg: Config,
    providers: dict[str, DreamProvider],
    store: MemoryStore,
    context: dict[str, Any],
    seed_ids: list[str] | None = None,
) -> StageOutput:
    route = cfg.route_for(stage)
    params = cfg.stage_params(stage)
    if route.provider not in providers:
        raise RuntimeError(
            f"Stage '{stage}' wants provider '{route.provider}' but it is not "
            f"configured (missing API key?)."
        )
    provider = providers[route.provider]

    sp = STAGE_PROMPTS[stage]
    system = sp["system"]
    user = sp["user"].format(**context)

    result = await provider.complete(
        model=route.model,
        system=system,
        messages=[Message(role="user", content=user)],
        temperature=params.temperature,
        top_p=params.top_p,
        max_tokens=params.max_tokens,
    )

    store.add_dream(
        DreamRecord(
            stage=stage,
            cycle=cycle,
            content=result.text,
            seed_ids=seed_ids or [],
            provider=result.provider,
            model=result.model,
        )
    )
    return StageOutput(
        stage=stage,
        text=result.text,
        provider=result.provider,
        model=result.model,
        seed_ids=seed_ids or [],
    )
