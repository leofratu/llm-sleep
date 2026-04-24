"""JSONL-backed episodic + semantic memory.

This is a deliberately simple POC store: no vector DB dependency. It keeps
the project installable with just `pip install .` while showing the right
abstractions. Swap for Chroma/Qdrant/pgvector later without changing callers.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class EpisodicMemory:
    """One concrete experience the agent had while awake."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    ts: float = field(default_factory=time.time)
    content: str = ""                # narrative/state description
    action: str | None = None
    outcome: str | None = None
    reward: float = 0.0              # scalar outcome signal (can be negative)
    expected_reward: float = 0.0     # agent's predicted reward BEFORE the event
    valence: float = 0.0             # -1 bad .. +1 good
    arousal: float = 0.0             # 0 calm .. 1 intense
    tags: list[str] = field(default_factory=list)
    rehearsal_count: int = 0         # how often it's been dreamt about


@dataclass
class SemanticFact:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    ts: float = field(default_factory=time.time)
    fact: str = ""
    sources: list[str] = field(default_factory=list)  # episodic ids
    confidence: float = 0.5


@dataclass
class DreamRecord:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    ts: float = field(default_factory=time.time)
    stage: str = ""
    cycle: int = 0
    content: str = ""
    seed_ids: list[str] = field(default_factory=list)
    provider: str = ""
    model: str = ""


class MemoryStore:
    """File-per-kind JSONL store under a run directory."""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.episodic_path = self.root / "episodic.jsonl"
        self.semantic_path = self.root / "semantic.jsonl"
        self.dream_path = self.root / "dreams.jsonl"
        self.reflection_path = self.root / "reflections.jsonl"

    # ---------- episodic ----------
    def add_episodic(self, mem: EpisodicMemory) -> EpisodicMemory:
        self._append(self.episodic_path, asdict(mem))
        return mem

    def all_episodic(self) -> list[EpisodicMemory]:
        return [EpisodicMemory(**d) for d in self._read(self.episodic_path)]

    def bump_rehearsal(self, ids: list[str]) -> None:
        rows = self._read(self.episodic_path)
        touched = set(ids)
        for r in rows:
            if r["id"] in touched:
                r["rehearsal_count"] = r.get("rehearsal_count", 0) + 1
        self._write(self.episodic_path, rows)

    # ---------- semantic ----------
    def add_fact(self, fact: SemanticFact) -> SemanticFact:
        self._append(self.semantic_path, asdict(fact))
        return fact

    def all_facts(self) -> list[SemanticFact]:
        return [SemanticFact(**d) for d in self._read(self.semantic_path)]

    # ---------- dreams ----------
    def add_dream(self, d: DreamRecord) -> DreamRecord:
        self._append(self.dream_path, asdict(d))
        return d

    def all_dreams(self) -> list[DreamRecord]:
        return [DreamRecord(**d) for d in self._read(self.dream_path)]

    # ---------- reflections ----------
    def add_reflection(self, r: dict) -> None:
        self._append(self.reflection_path, r)

    # ---------- helpers ----------
    @staticmethod
    def _append(path: Path, obj: dict) -> None:
        with path.open("a") as f:
            f.write(json.dumps(obj) + "\n")

    @staticmethod
    def _read(path: Path) -> list[dict]:
        if not path.exists():
            return []
        with path.open() as f:
            return [json.loads(line) for line in f if line.strip()]

    @staticmethod
    def _write(path: Path, rows: list[dict]) -> None:
        with path.open("w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
