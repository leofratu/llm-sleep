# Dream Emulator (`llm-sleep`)

Use the `llm-sleep` dream emulator to give an AI agent biologically-inspired
offline processing: salience-weighted memory replay, multi-stage sleep
cycles (N1 → N2 → N3 → REM ± nightmare ± lucid), and a morning
reflection that emits a structured consolidation plan.

## When to use this skill

Invoke this skill when the user asks to:

- **"Let the agent sleep / dream / consolidate"** over recent work
- **"Run a nightmare / stress test"** targeted at the agent's weak points
- **"Reflect on today"** and produce a consolidation plan
- **Distill episodic memories into semantic rules** (N3 SWS consolidation)
- **Rehearse a goal** through a lucid-dream stage

If the user asks "can you dream?", this skill is the thing that does it.

## Prerequisites

The `llm-sleep` package must be importable and at least one of these env
vars set: `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`, or
`CUSTOM_BASE_URL` + `CUSTOM_API_KEY`.

```bash
pip install -e /path/to/llm-sleep
dreamer providers    # verify which providers are live
```

## Usage

### 1. Record what happened today (episodic memory)

```bash
dreamer remember "Debugged async fixture leak; traced to unclosed loop." \
  --reward 0.8 --expected-reward 0.4 \
  --valence 0.7 --arousal 0.5 \
  --tags "async,testing" \
  --run runs/<agent-id>
```

Or batch-load a JSONL file:

```bash
dreamer remember-batch today.jsonl --run runs/<agent-id>
```

### 2. Put the agent to sleep

```bash
dreamer sleep \
  --run runs/<agent-id> \
  --cycles 3 \
  --goals "<comma-separated current goals>" \
  --obstacles "<comma-separated known obstacles>" \
  --competence "<one-line description of skill level>"
```

This runs 3 full NREM → REM cycles, may emit nightmares if the agent has
unresolved negative-valence memories, and ends with a morning reflection
dumped to `runs/<agent-id>/reflections.jsonl`.

### 3. Read the morning journal

```bash
dreamer reflect --run runs/<agent-id>
```

## Choosing a routing profile

| Profile       | When to use                                    |
|---------------|------------------------------------------------|
| default       | Balanced: haiku for NREM, sonnet for REM/lucid, opus for reflection |
| cheap         | Cost-sensitive (nano/flash-lite everywhere)    |
| frontier      | Best quality regardless of cost                |
| cross_vendor  | Ablations — each vendor gets one stage         |
| local         | Fully offline via Ollama / LM Studio / vLLM    |

Pick with `--config dreamer/profiles.yaml` (see `dreamer/profiles.yaml`).

## Output schema

Each run produces JSONL files under `runs/<agent-id>/`:

- `episodic.jsonl` — raw experiences (the input)
- `semantic.jsonl` — distilled facts/rules (written during N3)
- `dreams.jsonl` — every stage's output tagged with cycle + model
- `reflections.jsonl` — morning consolidation plan

The reflection JSON is the authoritative output. Its `consolidation_plan`
contains `keep / compress / forget / train_on / value_changes`. Values
changes are *never* auto-applied — surface them to the user.

## Important

- **Nightmares are deliberate**. If the user is uncomfortable with
  adversarial scenarios, pass `--config` pointing at a YAML with
  `nightmare_enabled: false`.
- **This is a POC**. It modifies a retrieval store, not model weights.
  Skill updates (LoRA / fine-tune) are out of scope here.
- **Cost**: a 3-cycle night with the default profile is roughly 8–14
  model calls. Use the `cheap` profile for dev loops.
