---
name: llm-sleep
description: |
  Run a biologically-inspired dream cycle over an AI agent's episodic
  memories. Invoke when the user asks to "sleep", "dream", "consolidate",
  "reflect on today", "run a nightmare", or "stress-test weak points".
  Produces a morning reflection JSON with a consolidation plan.
triggers:
  - "put the agent to sleep"
  - "let it dream"
  - "consolidate memories"
  - "run a nightmare"
  - "lucid rehearse"
  - "morning reflection"
---

# llm-sleep OpenCode skill

## What this does

Runs the `dreamer` CLI to execute one "night" over the current agent's
episodic memory store. Each night is 3+ cycles of N1 → N2 → N3 → REM,
optionally ending with a nightmare (for unresolved negative affect) and
a lucid dream (goal rehearsal), plus a morning reflection that emits a
structured JSON consolidation plan.

## How to invoke

```bash
# 1. Verify providers
dreamer providers

# 2. Seed memories (idempotent; skip if already loaded)
dreamer remember-batch <path.jsonl> --run runs/<agent-id>

# 3. Sleep
dreamer sleep \
    --run runs/<agent-id> \
    --cycles 3 \
    --goals "<goal1, goal2>" \
    --obstacles "<obs1, obs2>" \
    --competence "<one-line description>"

# 4. Read the journal
dreamer reflect --run runs/<agent-id>
```

## Config profiles

Available via `--config dreamer/profiles.yaml`:

- `cheap` — nano/flash-lite everywhere, for dev loops
- `frontier` — best models everywhere
- `cross_vendor` — each provider gets one stage (good for ablations)
- `local` — fully offline through an OpenAI-compatible local server

## Output

All artifacts under `runs/<agent-id>/`:

```
episodic.jsonl       input memories
semantic.jsonl       distilled facts (written during N3)
dreams.jsonl         every stage output, tagged by cycle + model
reflections.jsonl    morning consolidation plans
```

## Rules

1. Never auto-apply `consolidation_plan.value_changes`. Surface to user.
2. Use `--cycles 1` for demos, 3–5 for real runs.
3. Warn if episodic memory is empty — dreams will be shallow.
4. Do not mix agents in one `runs/<id>` directory.
