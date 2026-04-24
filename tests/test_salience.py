"""Salience scoring tests."""
from __future__ import annotations

import time

from dreamer.memory.salience import score_memory
from dreamer.memory.store import EpisodicMemory

WEIGHTS = {
    "surprise": 1.0,
    "arousal": 0.8,
    "recency": 0.5,
    "forget_boost": 0.4,
    "goal_relevance": 0.7,
}


def _mem(**kw) -> EpisodicMemory:
    return EpisodicMemory(**kw)


def test_surprise_dominates_when_big():
    fresh = _mem(content="x", reward=1.0, expected_reward=-1.0, arousal=0.0)
    boring = _mem(content="y", reward=0.1, expected_reward=0.1, arousal=0.0)
    assert score_memory(fresh, WEIGHTS) > score_memory(boring, WEIGHTS)


def test_rehearsal_lowers_forget_boost():
    m = _mem(content="x")
    before = score_memory(m, WEIGHTS)
    m.rehearsal_count = 5
    after = score_memory(m, WEIGHTS)
    assert after < before


def test_goal_keyword_match_boosts_score():
    m = _mem(content="fix the unicode regex bug in the parser")
    without = score_memory(m, WEIGHTS, goal_keywords=[])
    with_ = score_memory(m, WEIGHTS, goal_keywords=["unicode"])
    assert with_ > without


def test_recency_decays_over_time():
    now = time.time()
    recent = _mem(content="x", ts=now)
    old = _mem(content="x", ts=now - 30 * 86400)
    assert score_memory(recent, WEIGHTS, now=now) > score_memory(
        old, WEIGHTS, now=now
    )
