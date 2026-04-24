"""Config loading tests — no network, no API keys required."""
from __future__ import annotations

from dreamer.config import load_config


def test_default_config_loads():
    cfg = load_config()
    assert cfg.num_cycles >= 1
    assert "default" in cfg.routing
    assert "rem" in cfg.stages


def test_stage_params_defaults_when_missing():
    cfg = load_config()
    # A stage not in YAML returns generic defaults, not an error.
    p = cfg.stage_params("some_unknown_stage")
    assert 0.0 <= p.temperature <= 2.0
    assert p.max_tokens > 0


def test_route_fallback_to_default():
    cfg = load_config()
    r = cfg.route_for("nonexistent_stage")
    assert r.provider
    assert r.model
