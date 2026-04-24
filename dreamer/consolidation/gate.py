"""Consolidation — applies a reflection's plan to memory.

Safety rules:
- FACTS may be auto-applied (low risk, RAG-style).
- SKILLS (weight updates, LoRA) require human review in this POC.
- VALUE/GOAL changes NEVER auto-apply. They are logged for a human.
"""

from __future__ import annotations

from typing import Any

from ..config import Config
from ..memory.store import MemoryStore


def apply_reflection(
    reflection: dict[str, Any],
    store: MemoryStore,
    cfg: Config,
) -> dict[str, Any]:
    plan = (reflection or {}).get("consolidation_plan", {})
    report = {"applied": [], "pending_review": [], "skipped": []}

    # Forget: we only *mark* episodes as forgotten in this POC (no deletion
    # without an explicit CLI flag), to keep the run reproducible.
    forget = plan.get("forget") or []
    if forget:
        report["pending_review"].append(
            {"kind": "forget", "count": len(forget), "ids": forget}
        )

    # Train-on list -> just flag; real LoRA/fine-tune is a separate pipeline.
    train = plan.get("train_on") or []
    if train:
        if cfg.auto_apply_skills:
            report["applied"].append(
                {"kind": "skills", "count": len(train)}
            )
        else:
            report["pending_review"].append(
                {"kind": "skills", "count": len(train), "items": train}
            )

    # Values / goals — never auto.
    values = plan.get("value_changes") or []
    if values:
        report["pending_review"].append(
            {"kind": "values", "items": values}
        )

    return report
