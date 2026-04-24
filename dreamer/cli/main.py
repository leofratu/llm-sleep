"""Typer-based CLI.

Subcommands:
  dreamer remember     add an episodic memory (JSON or flags)
  dreamer memories     list stored memories
  dreamer sleep        run a full night
  dreamer reflect      show the last reflection
  dreamer providers    show which providers are live
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich import print
from rich.console import Console
from rich.table import Table

from ..config import load_config
from ..memory.store import EpisodicMemory, MemoryStore
from ..orchestrator import run_night
from ..providers import build_providers
from ..consolidation import apply_reflection

app = typer.Typer(
    add_completion=False,
    help="llm-sleep — a dream emulator for AI agents.",
)
console = Console()


def _store(run_dir: Path) -> MemoryStore:
    return MemoryStore(run_dir)


@app.command()
def providers(config: Optional[Path] = typer.Option(None)):
    """List providers that are live in the current environment."""
    cfg = load_config(config)
    try:
        ps = build_providers(cfg)
    except RuntimeError as e:
        print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    t = Table("provider", "status", "default model for stages")
    routes = {p: [] for p in ps}
    for stage, r in cfg.routing.items():
        routes.setdefault(r.provider, []).append(f"{stage}:{r.model}")
    for name in ps:
        t.add_row(name, "[green]ready[/green]", ", ".join(routes.get(name, [])) or "-")
    console.print(t)


@app.command()
def remember(
    content: str = typer.Argument(..., help="what happened"),
    reward: float = 0.0,
    expected_reward: float = 0.0,
    valence: float = 0.0,
    arousal: float = 0.0,
    tags: str = "",
    run: Path = typer.Option(Path("runs/default"), help="run directory"),
):
    """Record a single episodic memory."""
    store = _store(run)
    m = EpisodicMemory(
        content=content,
        reward=reward,
        expected_reward=expected_reward,
        valence=valence,
        arousal=arousal,
        tags=[t for t in tags.split(",") if t],
    )
    store.add_episodic(m)
    print(f"[green]remembered[/green] {m.id}")


@app.command()
def remember_batch(
    path: Path = typer.Argument(..., exists=True, readable=True),
    run: Path = typer.Option(Path("runs/default")),
):
    """Load a JSONL file of episodic memories."""
    store = _store(run)
    n = 0
    with path.open() as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            store.add_episodic(EpisodicMemory(**d))
            n += 1
    print(f"[green]loaded {n} memories[/green]")


@app.command()
def memories(run: Path = typer.Option(Path("runs/default"))):
    """Show what the agent currently remembers."""
    store = _store(run)
    mems = store.all_episodic()
    t = Table("id", "reward", "valence", "arousal", "rehearsed", "content")
    for m in mems:
        t.add_row(
            m.id,
            f"{m.reward:+.2f}",
            f"{m.valence:+.2f}",
            f"{m.arousal:.2f}",
            str(m.rehearsal_count),
            (m.content[:80] + "…") if len(m.content) > 80 else m.content,
        )
    console.print(t)


@app.command()
def sleep(
    goals: str = typer.Option("", help="comma-separated agent goals"),
    obstacles: str = typer.Option("", help="comma-separated obstacles"),
    competence: str = typer.Option("intermediate", help="free-text competence level"),
    run: Path = typer.Option(Path("runs/default")),
    config: Optional[Path] = typer.Option(None),
    cycles: Optional[int] = typer.Option(None, help="override number of cycles"),
):
    """Put the agent to sleep for one night."""
    cfg = load_config(config)
    if cycles is not None:
        cfg.num_cycles = cycles
    providers_ = build_providers(cfg)
    store = _store(run)

    agent_state = {
        "goals": [g.strip() for g in goals.split(",") if g.strip()],
        "obstacles": [o.strip() for o in obstacles.split(",") if o.strip()],
        "competence": competence,
    }

    result = asyncio.run(
        run_night(
            cfg=cfg,
            providers=providers_,
            store=store,
            agent_state=agent_state,
        )
    )

    console.rule("[bold]Consolidation plan")
    report = apply_reflection(result.get("reflection") or {}, store, cfg)
    print(report)
    console.rule("[bold green]Sleep complete")
    print(f"[dim]Artifacts at {run}[/dim]")


@app.command()
def reflect(run: Path = typer.Option(Path("runs/default"))):
    """Show the most recent morning reflection."""
    path = run / "reflections.jsonl"
    if not path.exists():
        print("[yellow]no reflections yet[/yellow]")
        raise typer.Exit(0)
    last = None
    with path.open() as f:
        for line in f:
            if line.strip():
                last = json.loads(line)
    print(last)


if __name__ == "__main__":
    app()
