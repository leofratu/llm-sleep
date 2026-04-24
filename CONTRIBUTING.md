# Contributing

`llm-sleep` is a proof-of-concept. PRs welcome, especially around:

1. **New providers** (any OpenAI/Anthropic-compatible endpoint).
2. **Better salience functions** — the current weighting is a starting
   point, not a claim about what's optimal.
3. **Evaluation harness** — the `dreamer/evaluation/` directory is a
   scaffold. Downstream-task A/B protocols would turn this from
   "interesting" into "publishable".
4. **Actual consolidation** — LoRA training on dream rollouts, with the
   safety gate kept intact.

## Dev setup

```bash
git clone https://github.com/leofratu/llm-sleep.git
cd llm-sleep
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
ruff check dreamer tests
```

## Style

- `ruff` for lint, defaults.
- Type hints on public APIs.
- Docstrings explain *why*, not *what*.
- Prompts live in `dreamer/stages/prompts.py` so prompt iteration is
  one-file-diff reviewable.

## Adding a provider

1. New module under `dreamer/providers/<name>.py`.
2. Implement `complete(...)` per the `DreamProvider` protocol.
3. Wire it in `dreamer/providers/__init__.py` behind an env-var gate.
4. Add at least one test under `tests/` that uses the fake-provider
   pattern from `tests/test_orchestrator_fake.py`.

## Adding a stage

1. New key in `dreamer/stages/prompts.py` with `system` + `user`.
2. New entry in `config.default.yaml` under `stages` and `routing`.
3. Wire the call in `dreamer/orchestrator/scheduler.py` at the point in
   the cycle where it belongs.

## Commit style

Conventional Commits. One concept per commit; smaller is better than
larger when reviewing prompt changes.
