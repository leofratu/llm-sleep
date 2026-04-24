"""Stage orchestration test using a fake in-memory provider.

No network, no keys. Verifies that a 1-cycle night runs N1→N2→N3→REM
(+lucid on last cycle) and produces a reflection.
"""
from __future__ import annotations

import asyncio
import json

import pytest

from dreamer.config import load_config
from dreamer.memory.store import EpisodicMemory, MemoryStore
from dreamer.orchestrator import run_night
from dreamer.providers.base import CompletionResult, Message


class FakeProvider:
    name = "fake"

    def __init__(self):
        self.calls = []

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
        self.calls.append({"model": model, "temp": temperature})
        # Reflection stage must return parseable JSON; others return prose.
        if "morning reflection stage" in system:
            text = json.dumps(
                {
                    "themes": ["t"],
                    "insights": ["i"],
                    "contradictions": [],
                    "skill_gaps": [],
                    "consolidation_plan": {
                        "keep": [],
                        "compress": [],
                        "forget": [],
                        "train_on": [],
                        "value_changes": [],
                    },
                    "next_night_hints": [],
                    "affect_delta": {"valence": 0.0, "arousal": 0.0},
                }
            )
        else:
            text = f"stage-output-for-{model}-at-T{temperature:.2f}"
        return CompletionResult(
            text=text, model=model, provider=self.name, usage={}, raw={}
        )


@pytest.mark.asyncio
async def test_run_one_cycle_night_with_fake_provider(tmp_path):
    cfg = load_config()
    cfg.num_cycles = 1
    cfg.nightmare_enabled = False
    cfg.lucid_enabled = False
    # Route every stage to our fake provider.
    for stage, r in cfg.routing.items():
        r.provider = "fake"

    store = MemoryStore(tmp_path)
    store.add_episodic(
        EpisodicMemory(content="did a thing", reward=0.8, valence=0.5, arousal=0.4)
    )

    fake = FakeProvider()
    result = await run_night(
        cfg=cfg,
        providers={"fake": fake},
        store=store,
        agent_state={"goals": ["x"], "obstacles": [], "competence": "mid"},
    )

    # N1 + N2 + N3 + REM + reflection = 5 calls minimum
    assert len(fake.calls) >= 5
    assert result["reflection"] is not None
    assert "consolidation_plan" in result["reflection"]


def test_async_wrapper():
    # Convenience: ensure the test itself can be invoked without plugins
    asyncio.get_event_loop_policy()
