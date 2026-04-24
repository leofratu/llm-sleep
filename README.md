# llm-sleep

**A dream emulator for AI agents.** Biologically-inspired sleep stages,
targeted nightmares, and morning reflection — powered by any
Anthropic / Google / OpenAI-compatible endpoint.

> *"Sleep is the price we pay for plasticity."* — Giulio Tononi

This is a **proof-of-concept** that treats an AI agent's downtime as
structured offline compute: the agent replays its day, compresses it,
dreams over it, stress-tests itself in nightmares, and wakes with a
consolidation plan. Every stage is an LLM call with its own temperature,
system prompt, and output schema.

## What it does

Given an agent with a pile of episodic memories (things that happened to
it while "awake"), `llm-sleep` runs a **night** consisting of 3–6 sleep
cycles. Each cycle moves through:

```
N1 drift  →  N2 spindle  →  N3 deep  →  REM  →  (nightmare?)  →  (lucid?)
T=0.3        T=0.4         T=0.2      T=1.0    T=1.1            T=0.8
```

and ends with a **morning reflection** that emits a JSON consolidation
plan: what to keep, compress, forget, train on, and what value-level
proposals need human review.

## Install

```bash
git clone https://github.com/leofratu/llm-sleep.git
cd llm-sleep
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env   # fill in at least one API key
```

`llm-sleep` works with **any** provider you have a key for. Set zero keys
and it refuses to start; set one and only stages routed to that provider
run. Edit `dreamer/config.default.yaml` (or pass `--config`) to reroute.

## Quickstart

```bash
# Which providers did I activate?
dreamer providers

# Seed some episodic memories (things the agent did today)
dreamer remember-batch examples/seed_memories.jsonl --run runs/demo

# Put the agent to sleep
dreamer sleep \
  --run runs/demo \
  --cycles 3 \
  --goals "write safer code, handle unicode correctly" \
  --obstacles "overconfidence on regex, overengineering" \
  --competence "strong at refactoring, weak at subtle async bugs"

# Inspect the morning journal
dreamer reflect --run runs/demo
```

Artifacts for each run land under `runs/<name>/`:

```
runs/demo/
├── episodic.jsonl      # what the agent remembers
├── semantic.jsonl      # rules/facts distilled during N3
├── dreams.jsonl        # every stage output, tagged by cycle
└── reflections.jsonl   # morning consolidation plans
```

## Provider routing

Every stage is routed independently. Use a cheap model for NREM (lots of
throughput, boring work) and a frontier model for REM / reflection
(creativity + reasoning). See `dreamer/config.default.yaml`.

| Provider   | Env var                | Endpoint                                                  | Notes |
|------------|------------------------|-----------------------------------------------------------|-------|
| Anthropic  | `ANTHROPIC_API_KEY`    | `https://api.anthropic.com`                               | Native Messages API |
| Google     | `GEMINI_API_KEY`       | `https://generativelanguage.googleapis.com/v1beta/openai` | OpenAI-compat mode  |
| OpenAI     | `OPENAI_API_KEY`       | `https://api.openai.com/v1`                               | Chat Completions    |
| Custom     | `CUSTOM_API_KEY` + `CUSTOM_BASE_URL` | anything OpenAI-compatible                  | Groq / Together / vLLM / Ollama / OpenRouter / LM Studio |

## As a skill for coding agents

`llm-sleep` ships with ready-to-use skill manifests under `skills/` for:

- **Claude Code** (`skills/claude-code/SKILL.md`)
- **Codex CLI** (`skills/codex/AGENTS.md`)
- **OpenCode** (`skills/opencode/skill.md`)

See [`skills/README.md`](skills/README.md) for how to install each.

## Why this is interesting

See [`docs/BIOLOGY.md`](docs/BIOLOGY.md) for the full "how this mimics
real dreaming" write-up and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
for the system design.

Short version: the pieces already exist in the ML literature —
experience replay, world models, curriculum learning, self-distillation.
Nobody has wired them together behind a single biologically-grounded
interface. This repo is a minimum honest attempt at that.

## License

MIT. See [`LICENSE`](LICENSE).
