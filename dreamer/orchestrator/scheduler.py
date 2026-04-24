"""Night scheduler — runs cycles of NREM → REM (± nightmare ± lucid),
then a morning reflection.

This is the heart of the emulator: it's where the biological sleep
architecture becomes code. REM lengthens each cycle, NREM-deep shortens,
and nightmares are conditional on unresolved negative affect.
"""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console

from ..config import Config
from ..memory.salience import score_memory
from ..memory.store import EpisodicMemory, MemoryStore, SemanticFact
from ..providers import DreamProvider
from ..stages import run_stage, StageOutput

console = Console()


def _format_memories(mems: list[EpisodicMemory], limit: int = 12) -> str:
    lines = []
    for m in mems[:limit]:
        lines.append(
            f"- [{m.id}] reward={m.reward:+.2f} valence={m.valence:+.2f} "
            f"arousal={m.arousal:.2f} :: {m.content[:160]}"
        )
    return "\n".join(lines) if lines else "(no memories yet)"


def _format_facts(facts: list[SemanticFact], limit: int = 8) -> str:
    if not facts:
        return "(empty)"
    return "\n".join(f"- {f.fact}" for f in facts[:limit])


def _has_unresolved_trauma(mems: list[EpisodicMemory]) -> bool:
    return any(m.valence < -0.3 and m.rehearsal_count < 2 for m in mems)


def _top_negative(mems: list[EpisodicMemory], k: int) -> list[EpisodicMemory]:
    return sorted(mems, key=lambda m: m.valence)[:k]


async def run_night(
    *,
    cfg: Config,
    providers: dict[str, DreamProvider],
    store: MemoryStore,
    agent_state: dict[str, Any],
) -> dict[str, Any]:
    """Run a full night. Returns the morning reflection dict."""
    goals = agent_state.get("goals", [])
    competence = agent_state.get("competence", "unspecified")
    obstacles = agent_state.get("obstacles", [])

    all_mems = store.all_episodic()
    goal_kw = goals if isinstance(goals, list) else [str(goals)]
    scored = sorted(
        all_mems,
        key=lambda m: score_memory(m, cfg.salience, goal_keywords=goal_kw),
        reverse=True,
    )

    night_log: list[dict[str, Any]] = []

    for cycle_idx in range(cfg.num_cycles):
        console.rule(f"[bold cyan]Cycle {cycle_idx + 1}/{cfg.num_cycles}")

        cycle_seeds = scored[: 6 + cycle_idx]  # slightly wider net each cycle
        seed_ids = [m.id for m in cycle_seeds]

        # ---- NREM descent ----
        n1 = await run_stage(
            stage="n1_drift",
            cycle=cycle_idx,
            cfg=cfg,
            providers=providers,
            store=store,
            context={
                "goals": ", ".join(goal_kw) or "(none)",
                "memories": _format_memories(cycle_seeds),
            },
            seed_ids=seed_ids,
        )
        _log(night_log, n1)

        n2 = await run_stage(
            stage="n2_spindle",
            cycle=cycle_idx,
            cfg=cfg,
            providers=providers,
            store=store,
            context={"n1_output": n1.text},
            seed_ids=seed_ids,
        )
        _log(night_log, n2)

        n3 = await run_stage(
            stage="n3_deep",
            cycle=cycle_idx,
            cfg=cfg,
            providers=providers,
            store=store,
            context={
                "n2_output": n2.text,
                "semantic": _format_facts(store.all_facts()),
            },
            seed_ids=seed_ids,
        )
        _log(night_log, n3)

        # Try to extract facts from the N3 JSON (best-effort).
        _absorb_n3_facts(n3.text, seed_ids, store, cfg)

        # ---- REM ----
        rem_turns = int(cfg.base_rem_turns * (1 + 0.3 * cycle_idx))
        drift_note = (
            "This is a later cycle — allow more surreal imagery."
            if cycle_idx >= cfg.num_cycles - 1
            else "This is an early cycle — stay closer to literal memory."
        )
        rem = await run_stage(
            stage="rem",
            cycle=cycle_idx,
            cfg=cfg,
            providers=providers,
            store=store,
            context={
                "seeds": _format_memories(cycle_seeds, limit=6),
                "semantic": _format_facts(store.all_facts()),
                "goals": ", ".join(goal_kw) or "(none)",
                "turns": rem_turns,
                "cycle_drift_note": drift_note,
            },
            seed_ids=seed_ids,
        )
        _log(night_log, rem)

        # ---- Nightmare (conditional) ----
        if (
            cfg.nightmare_enabled
            and cycle_idx >= cfg.nightmare_min_cycle
            and _has_unresolved_trauma(all_mems)
        ):
            trauma = _top_negative(all_mems, cfg.nightmare_trauma_seed_k)
            nm = await run_stage(
                stage="nightmare",
                cycle=cycle_idx,
                cfg=cfg,
                providers=providers,
                store=store,
                context={
                    "trauma_seeds": _format_memories(trauma, limit=len(trauma)),
                    "competence": competence,
                    "target_rate": cfg.nightmare_target_success_rate,
                },
                seed_ids=[m.id for m in trauma],
            )
            _log(night_log, nm)

        # ---- Lucid (last cycle only) ----
        if cfg.lucid_enabled and cycle_idx == cfg.num_cycles - 1:
            lucid = await run_stage(
                stage="lucid",
                cycle=cycle_idx,
                cfg=cfg,
                providers=providers,
                store=store,
                context={
                    "goals": ", ".join(goal_kw) or "(none)",
                    "obstacles": "\n".join(f"- {o}" for o in obstacles) or "(none)",
                },
                seed_ids=seed_ids,
            )
            _log(night_log, lucid)

        # Bump rehearsal counts so under-rehearsed memories get priority later.
        store.bump_rehearsal(seed_ids)

    # ---- Morning reflection ----
    console.rule("[bold magenta]Morning reflection")
    night_summary = "\n\n".join(
        f"[{e['stage']} · cycle {e['cycle']} · {e['provider']}/{e['model']}]\n"
        f"{e['text'][:600]}"
        for e in night_log
    )
    reflection = await run_stage(
        stage="reflection",
        cycle=cfg.num_cycles,
        cfg=cfg,
        providers=providers,
        store=store,
        context={
            "night_summary": night_summary,
            "agent_state": json.dumps(agent_state, ensure_ascii=False),
        },
    )
    parsed = _safe_json(reflection.text)
    store.add_reflection(
        {
            "ts": __import__("time").time(),
            "provider": reflection.provider,
            "model": reflection.model,
            "raw": reflection.text,
            "parsed": parsed,
        }
    )
    return {
        "night_log": night_log,
        "reflection_raw": reflection.text,
        "reflection": parsed,
    }


# ---------- helpers ----------
def _log(night_log: list[dict], s: StageOutput) -> None:
    console.print(
        f"[dim]{s.stage} · {s.provider}/{s.model}[/dim] "
        f"— {len(s.text)} chars"
    )
    night_log.append(
        {
            "stage": s.stage,
            "cycle": 0,  # not important for summary
            "provider": s.provider,
            "model": s.model,
            "text": s.text,
        }
    )


def _safe_json(text: str) -> dict:
    """Best-effort JSON extraction from a model response."""
    import re

    text = text.strip()
    # strip ```json fences if present
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = m.group(1) if m else text
    # fall back to the widest {...} substring
    if not candidate.lstrip().startswith("{"):
        i, j = candidate.find("{"), candidate.rfind("}")
        if i >= 0 and j > i:
            candidate = candidate[i : j + 1]
    try:
        return json.loads(candidate)
    except Exception:
        return {"_parse_error": True, "_raw": text[:500]}


def _absorb_n3_facts(
    text: str, source_ids: list[str], store: MemoryStore, cfg: Config
) -> None:
    if not cfg.auto_apply_facts:
        return
    data = _safe_json(text)
    if data.get("_parse_error"):
        return
    for f in data.get("facts", []):
        if not isinstance(f, dict) or "fact" not in f:
            continue
        store.add_fact(
            SemanticFact(
                fact=f["fact"],
                sources=f.get("sources") or source_ids,
                confidence=float(f.get("confidence", 0.6)),
            )
        )
