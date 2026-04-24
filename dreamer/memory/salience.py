"""Salience scoring — decides which memories get replayed tonight.

Direct analog of hippocampal replay prioritization: surprising, emotional,
recent, under-rehearsed, and goal-relevant experiences win the lottery.

score = w_surprise * |reward - expected|
      + w_arousal  * arousal
      + w_recency  * exp(-Δdays)
      + w_forget   * 1 / (1 + rehearsal_count)
      + w_goal     * goal_relevance
"""

from __future__ import annotations

import math
import time

from .store import EpisodicMemory


def score_memory(
    m: EpisodicMemory,
    weights: dict,
    goal_keywords: list[str] | None = None,
    now: float | None = None,
) -> float:
    now = now or time.time()
    goal_keywords = goal_keywords or []

    w_surprise = weights.get("surprise", 1.0)
    w_arousal = weights.get("arousal", 0.8)
    w_recency = weights.get("recency", 0.5)
    w_forget = weights.get("forget_boost", 0.4)
    w_goal = weights.get("goal_relevance", 0.7)

    surprise = abs(m.reward - m.expected_reward)
    arousal = max(0.0, min(1.0, m.arousal))
    days = max(0.0, (now - m.ts) / 86400.0)
    recency = math.exp(-days / 3.0)  # half-life ~2 days
    forget = 1.0 / (1.0 + m.rehearsal_count)

    hay = (m.content + " " + (m.outcome or "")).lower()
    goal = 1.0 if any(k.lower() in hay for k in goal_keywords) else 0.0

    return (
        w_surprise * surprise
        + w_arousal * arousal
        + w_recency * recency
        + w_forget * forget
        + w_goal * goal
    )
