"""Configuration loading & schema.

A single `Config` object is passed everywhere. Users may pass a custom
YAML path; otherwise we fall back to `config.default.yaml` in this package.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

PACKAGE_DIR = Path(__file__).parent
DEFAULT_CONFIG = PACKAGE_DIR / "config.default.yaml"


@dataclass
class StageParams:
    temperature: float = 0.7
    top_p: float = 0.95
    max_tokens: int = 800


@dataclass
class Route:
    provider: str
    model: str


@dataclass
class Config:
    raw: dict[str, Any]

    # night
    num_cycles: int = 3
    base_rem_turns: int = 4
    lucid_enabled: bool = True
    nightmare_enabled: bool = True
    nightmare_min_cycle: int = 1

    stages: dict[str, StageParams] = field(default_factory=dict)
    routing: dict[str, Route] = field(default_factory=dict)
    salience: dict[str, float] = field(default_factory=dict)
    nightmare_target_success_rate: float = 0.35
    nightmare_max_attempts: int = 3
    nightmare_trauma_seed_k: int = 3

    auto_apply_facts: bool = True
    auto_apply_skills: bool = False
    auto_apply_values: bool = False

    def route_for(self, stage: str) -> Route:
        return self.routing.get(stage) or self.routing["default"]

    def stage_params(self, stage: str) -> StageParams:
        return self.stages.get(stage, StageParams())


def load_config(path: str | Path | None = None) -> Config:
    load_dotenv(override=False)
    p = Path(path) if path else DEFAULT_CONFIG
    with open(p) as f:
        raw = yaml.safe_load(f)

    night = raw.get("night", {})
    stages_raw = raw.get("stages", {})
    routing_raw = raw.get("routing", {})
    nm = raw.get("nightmare", {})
    cons = raw.get("consolidation", {})

    stages = {k: StageParams(**v) for k, v in stages_raw.items()}
    routing = {k: Route(**v) for k, v in routing_raw.items()}
    if "default" not in routing:
        raise ValueError("config.routing.default is required")

    return Config(
        raw=raw,
        num_cycles=night.get("num_cycles", 3),
        base_rem_turns=night.get("base_rem_turns", 4),
        lucid_enabled=night.get("lucid_enabled", True),
        nightmare_enabled=night.get("nightmare_enabled", True),
        nightmare_min_cycle=night.get("nightmare_min_cycle", 1),
        stages=stages,
        routing=routing,
        salience=raw.get("salience", {}),
        nightmare_target_success_rate=nm.get("target_success_rate", 0.35),
        nightmare_max_attempts=nm.get("max_attempts", 3),
        nightmare_trauma_seed_k=nm.get("trauma_seed_k", 3),
        auto_apply_facts=cons.get("auto_apply_facts", True),
        auto_apply_skills=cons.get("auto_apply_skills", False),
        auto_apply_values=cons.get("auto_apply_values", False),
    )


def env(name: str, default: str | None = None) -> str | None:
    v = os.environ.get(name, default)
    return v if v else None
