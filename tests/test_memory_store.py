"""Memory store round-trip tests."""
from __future__ import annotations

from dreamer.memory.store import (
    DreamRecord,
    EpisodicMemory,
    MemoryStore,
    SemanticFact,
)


def test_episodic_round_trip(tmp_path):
    store = MemoryStore(tmp_path)
    m = store.add_episodic(EpisodicMemory(content="hello", reward=0.5))
    assert m.id
    rows = store.all_episodic()
    assert len(rows) == 1
    assert rows[0].content == "hello"


def test_rehearsal_bump(tmp_path):
    store = MemoryStore(tmp_path)
    m = store.add_episodic(EpisodicMemory(content="hi"))
    store.bump_rehearsal([m.id])
    store.bump_rehearsal([m.id])
    assert store.all_episodic()[0].rehearsal_count == 2


def test_semantic_and_dream_logs(tmp_path):
    store = MemoryStore(tmp_path)
    store.add_fact(SemanticFact(fact="unicode is hard", confidence=0.9))
    store.add_dream(
        DreamRecord(stage="rem", cycle=0, content="vivid", provider="p", model="m")
    )
    assert len(store.all_facts()) == 1
    assert len(store.all_dreams()) == 1
