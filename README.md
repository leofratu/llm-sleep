<div align="center">

# llm-sleep

### A dream emulator for AI agents

**Biologically-inspired sleep stages · targeted nightmares · morning reflection**
**Powered by any Anthropic / Google / OpenAI-compatible endpoint**

[![CI](https://github.com/leofratu/llm-sleep/actions/workflows/ci.yml/badge.svg)](https://github.com/leofratu/llm-sleep/actions)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-proof--of--concept-orange)](docs/BIOLOGY.md)

[**Quickstart**](#quickstart) · [**Architecture**](#architecture) · [**How it mimics dreams**](docs/BIOLOGY.md) · [**Skills**](#use-it-as-a-skill) · [**FAQ**](#faq)

</div>

---

> *"Sleep is the price we pay for plasticity."* — Giulio Tononi

`llm-sleep` treats an AI agent's downtime as **structured offline compute**. The agent replays its day, clusters what happened, compresses episodes into durable rules, dreams over them, stress-tests itself in targeted nightmares, and wakes with a JSON consolidation plan. Every stage is an LLM call with its own temperature, prompt, and output schema — and every stage can be routed to a different provider/model.

## Table of contents

- [Why this exists](#why-this-exists)
- [At a glance](#at-a-glance)
- [The night, in one picture](#the-night-in-one-picture)
- [Install](#install)
- [Quickstart](#quickstart)
- [The seven stages](#the-seven-stages)
- [Provider matrix](#provider-matrix)
- [Routing profiles](#routing-profiles)
- [Architecture](#architecture)
- [Memory model](#memory-model)
- [Salience: which memories get replayed](#salience-which-memories-get-replayed)
- [Nightmares as curriculum](#nightmares-as-curriculum)
- [Morning reflection contract](#morning-reflection-contract)
- [Use it as a skill](#use-it-as-a-skill)
- [CLI reference](#cli-reference)
- [Testing](#testing)
- [Evaluation plan](#evaluation-plan)
- [Roadmap](#roadmap)
- [FAQ](#faq)
- [Citation](#citation)
- [License](#license)

---

## Why this exists

The individual ingredients of "AI dreaming" already exist in the machine-learning literature. Nobody has wired them together behind a single, biologically-grounded interface:

| Dream function (biology)         | Existing ML analog                                              |
|----------------------------------|-----------------------------------------------------------------|
| Hippocampal replay               | Prioritized Experience Replay (Schaul et al., 2016)             |
| World simulation during REM      | World Models / Dreamer V1–V3 (Ha & Schmidhuber; Hafner et al.)  |
| Generative recombination         | Diffusion / VAEs / LLM narrative sampling                       |
| Synaptic downscaling             | Weight decay, LoRA pruning, forgetting curves                   |
| Offline curriculum               | Self-play, adversarial scenario generation                      |
| Memory consolidation             | Self-distillation, RAG schema extraction                        |

`llm-sleep` is a minimum honest attempt to unify these behind a biological sleep architecture so the pieces can be studied together. It is a **proof of concept**, not a production system — see [`docs/BIOLOGY.md`](docs/BIOLOGY.md) for an honest "where the analogy breaks" section.

## At a glance

```text
Episodic memories  ─►  Salience sampling  ─►  N1  N2  N3  REM   (+ nightmare?)  (+ lucid?)
  (what happened           (surprise,           ↑───────cycle──────↑  repeated N times
   while awake)             arousal,                                    per "night"
                            recency,                                         │
                            forgetting,                                      ▼
                            goal-relevance)                         Morning reflection
                                                                    (JSON consolidation plan:
                                                                     keep / compress / forget /
                                                                     train_on / value_changes)
```

## The night, in one picture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                                  ONE NIGHT                                  │
│                                                                             │
│   cycle 1 ──────────────  cycle 2 ──────────────  cycle 3 ──────────── → 🌅 │
│   N1  N2  N3  REM          N1 N2 N3 REM (NM?)     N1 N2 N3 REM (NM?) LUCID │
│   T=0.3 0.4 0.2 1.0        0.3 0.4 0.2 1.0 1.1    0.3 0.4 0.2 1.0 1.1 0.8  │
│                                                                             │
│   REM grows each cycle (+30%)  │  Nightmares only once the agent has        │
│   NREM-deep shrinks each cycle │  unresolved negative-valence memories       │
│   Lucid fires on the last cycle│  Reflection runs once at dawn (strict JSON)│
└─────────────────────────────────────────────────────────────────────────────┘
```

## Install

```bash
git clone https://github.com/leofratu/leofratu/llm-sleep.git
cd llm-sleep
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env          # fill in at least one API key
```

Requires Python 3.10+. Development extras:

```bash
pip install -e ".[dev]"
pytest -q                     # 12 tests, no network required
```

## Quickstart

```bash
# 1. Which providers did my env activate?
dreamer providers

# 2. Seed a day's worth of episodic memories
dreamer remember-batch examples/seed_memories.jsonl --run runs/demo

# 3. Inspect
dreamer memories --run runs/demo

# 4. Sleep (3 cycles, ~8–14 model calls depending on nightmares)
dreamer sleep \
  --run runs/demo \
  --cycles 3 \
  --goals "write safer code, handle unicode correctly" \
  --obstacles "overconfidence on regex, overengineering" \
  --competence "strong at refactoring, weak at subtle async bugs"

# 5. Read the morning journal
dreamer reflect --run runs/demo
```

Everything lands under `runs/<name>/` as append-only JSONL — no database required.

```
runs/demo/
├── episodic.jsonl         # input: what the agent remembers
├── semantic.jsonl         # output: facts distilled during N3 slow-wave sleep
├── dreams.jsonl           # output: every stage's text, tagged with cycle + model
└── reflections.jsonl      # output: morning consolidation plans (JSON)
```

## The seven stages

Each stage is a focused LLM call with its own system prompt, temperature, and output contract. Temperature rises through the night — literally mirroring the shift from low-entropy NREM firing patterns to near-wake-like REM entropy.

| # | Stage          | Temp | What it does                                               | Biology analog                          |
|---|----------------|------|------------------------------------------------------------|-----------------------------------------|
| 1 | **N1 — Drift** | 0.3  | Select 3–5 fragments worth revisiting; no interpretation   | Transition to sleep, associative loosening |
| 2 | **N2 — Spindle** | 0.4 | Cluster fragments by theme; tag emotional tone             | Sleep spindles, memory tagging          |
| 3 | **N3 — Deep (SWS)** | 0.2 | Compress episodes → semantic facts + rules              | Slow-wave sleep, cortical consolidation |
| 4 | **REM**        | 1.0  | High-entropy narrative recombination of seeds + semantics  | REM dreaming, generative recombination  |
| 5 | **Nightmare**  | 1.1  | Adversarial scenario at the agent's competence frontier    | Fear-extinction replay, curriculum      |
| 6 | **Lucid**      | 0.8  | Goal-directed rehearsal in the final cycle                 | Lucid dreaming, mental simulation       |
| 7 | **Reflection** | 0.5  | Morning journal → strict JSON consolidation plan           | Waking meta-cognition                   |

All prompts live in [`dreamer/stages/prompts.py`](dreamer/stages/prompts.py) so prompt iteration is a one-file diff.

## Provider matrix

`llm-sleep` is fully provider-agnostic. Every stage is routed independently via config — use a cheap model for NREM and a frontier model for REM/reflection, or put every stage on a different vendor for ablations.

| Provider     | Env var(s)                                 | Endpoint                                                   | Native API            |
|--------------|--------------------------------------------|------------------------------------------------------------|-----------------------|
| **Anthropic**| `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL`  | `https://api.anthropic.com`                                | Messages API          |
| **Google**   | `GEMINI_API_KEY`, `GOOGLE_OPENAI_BASE_URL` | `https://generativelanguage.googleapis.com/v1beta/openai`  | OpenAI-compat         |
| **OpenAI**   | `OPENAI_API_KEY`, `OPENAI_BASE_URL`        | `https://api.openai.com/v1`                                | Chat Completions      |
| **Custom**   | `CUSTOM_API_KEY`, `CUSTOM_BASE_URL`        | anything OpenAI-compatible                                 | Chat Completions      |

**Works out of the box with:** Groq, Together, Fireworks, OpenRouter, Z.ai, DeepInfra, vLLM, Ollama, LM Studio, llama.cpp server, and any other OpenAI-compatible endpoint. Point `CUSTOM_BASE_URL` at the host; that's it.

Default model IDs (verified April 2026):

| Role                | Model                                |
|---------------------|--------------------------------------|
| Default / NREM      | `claude-haiku-4-7`                   |
| REM / Lucid         | `claude-sonnet-4-7`                  |
| Nightmare           | `gemini-3.1-pro-preview`             |
| Reflection          | `claude-opus-4-7`                    |

## Routing profiles

Pre-built profiles in [`dreamer/profiles.yaml`](dreamer/profiles.yaml):

| Profile        | Who it's for                                 | Rough cost per night |
|----------------|----------------------------------------------|----------------------|
| `default`      | Balanced: Claude mixed weights               | ≈ $0.10             |
| `cheap`        | Dev loops / CI                               | ≈ $0.01             |
| `frontier`     | Best quality regardless of cost              | ≈ $0.50             |
| `cross_vendor` | Every major provider gets one stage          | ≈ $0.15             |
| `local`        | Fully offline via Ollama / LM Studio / vLLM  | free (self-hosted)  |

> Costs are rough estimates for a 3-cycle night with ~500-token seeds. Your mileage will vary.

## Architecture

```text
┌───────────────────────────────────────────────────────────────────────┐
│                            dreamer.cli                                │
│      typer CLI: remember · memories · sleep · reflect · providers     │
└──────────────────────────────┬────────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────────┐
│                       orchestrator.scheduler                          │
│                                                                       │
│   run_night(cfg, providers, store, agent_state):                      │
│     for cycle in cfg.num_cycles:                                      │
│        N1 → N2 → N3 → REM → (nightmare?) → (lucid on last cycle)      │
│     reflection (morning)                                              │
└───┬──────────────────────┬────────────────────────┬──────────────────┘
    │                      │                        │
    ▼                      ▼                        ▼
┌─────────────┐   ┌──────────────────┐   ┌───────────────────────────┐
│   memory    │   │     stages       │   │        providers          │
│             │   │                  │   │                           │
│  store.py   │   │  runner.py       │   │  base.py  (Protocol)      │
│  salience   │   │  prompts.py      │   │  anthropic.py             │
│             │   │                  │   │  google.py   (OA-compat)  │
│             │   │                  │   │  openai.py                │
│             │   │                  │   │  custom.py   (any URL)    │
└─────────────┘   └──────────────────┘   └───────────────────────────┘
    │                                              │
    └──► JSONL under runs/<id>/                    └──► HTTPS (async)
```

Module responsibilities in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). Biology mapping in [`docs/BIOLOGY.md`](docs/BIOLOGY.md).

## Memory model

Three kinds of memory, matching the biological distinction:

```python
@dataclass
class EpisodicMemory:    # "I did X and Y happened"
    content: str
    reward: float
    expected_reward: float          # drives surprise signal
    valence: float                  # -1 bad .. +1 good
    arousal: float                  # 0 calm .. 1 intense
    tags: list[str]
    rehearsal_count: int            # how many nights this has been replayed

@dataclass
class SemanticFact:      # "X implies Y" (extracted in N3)
    fact: str
    sources: list[str]              # which episodes this came from
    confidence: float

@dataclass
class DreamRecord:       # every stage's output, for later analysis
    stage: str; cycle: int; content: str
    seed_ids: list[str]; provider: str; model: str
```

Storage is deliberately boring (JSONL) so the POC is installable with `pip install .`. The `MemoryStore` boundary is right for swapping in Chroma / Qdrant / pgvector without touching callers.

## Salience: which memories get replayed

The sampler is a direct analog of hippocampal replay prioritization. Surprising, emotional, recent, under-rehearsed, and goal-relevant experiences win the lottery:

```
score = w_surprise · |reward − expected_reward|
      + w_arousal  · arousal
      + w_recency  · exp(−Δdays / 2)
      + w_forget   · 1 / (1 + rehearsal_count)
      + w_goal     · goal_keyword_match
```

Weights are tunable in [`dreamer/config.default.yaml`](dreamer/config.default.yaml) under `salience:`. The `forget_boost` term implements the anti-forgetting-curve: memories that haven't been rehearsed recently get priority, matching experimental findings that replay targets weakly-encoded items later in the night.

## Nightmares as curriculum

Nightmares in the wild are often failed fear-extinction — the brain re-surfaces a threat to rehearse recovery, but sometimes gets stuck in it. `llm-sleep` uses this productively: the nightmare stage is explicitly targeted at the agent's **competence frontier**, aiming for ~35% in-dream success. This is Vygotsky's zone of proximal development, and it mirrors results from curriculum-learning RL.

- Too easy → no growth signal.
- Too hard → policy collapse / learned helplessness.
- Every nightmare must output a `RECOVERY_PATH` — the move that would have worked — which is the extinction-learning payload.

Trigger condition: the agent has episodic memories with `valence < −0.3` and `rehearsal_count < 2`. Configurable minimum cycle to prevent early-night distress.

## Morning reflection contract

The reflection stage is the only schema-critical output. It emits a strict JSON object:

```json
{
  "themes":         ["repeated motifs across dreams"],
  "insights":       ["new abstractions worth keeping"],
  "contradictions": ["beliefs that conflicted in dreams"],
  "skill_gaps":     ["what nightmares exposed"],
  "consolidation_plan": {
    "keep":          ["<episodic_id>"],
    "compress":      [{"ids": ["<id>"], "into": "<summary fact>"}],
    "forget":        ["<episodic_id>"],
    "train_on":      [{"dream_id": "...", "weight": 0.0}],
    "value_changes": ["..."]
  },
  "next_night_hints": ["what to dream about tomorrow"],
  "affect_delta": { "valence": 0.1, "arousal": -0.2 }
}
```

### Safety gate

The consolidation gate at [`dreamer/consolidation/gate.py`](dreamer/consolidation/gate.py) enforces:

| Plan element       | Default behavior       |
|--------------------|------------------------|
| `facts` (from N3)  | **Auto-applied** to semantic memory |
| `skills` (`train_on`) | **Pending human review** |
| `values` (`value_changes`) | **Never auto-applied** |

Dreams can propose; only waking review disposes.

## Use it as a skill

`llm-sleep` ships ready-to-install skill manifests for three coding-agent hosts:

| Host           | Manifest                                          | Install                                                   |
|----------------|---------------------------------------------------|-----------------------------------------------------------|
| Claude Code    | [`skills/claude-code/SKILL.md`](skills/claude-code/SKILL.md) | Copy to `~/.claude/skills/llm-sleep/SKILL.md`            |
| Codex CLI      | [`skills/codex/AGENTS.md`](skills/codex/AGENTS.md)           | Place at repo root or merge into existing `AGENTS.md`    |
| OpenCode       | [`skills/opencode/skill.md`](skills/opencode/skill.md)       | Copy to `~/.config/opencode/skills/llm-sleep/skill.md`   |

Each manifest includes trigger phrases, exact commands, the output contract, and the safety rules. See [`skills/README.md`](skills/README.md).

## CLI reference

```
dreamer providers                                  # show live providers
dreamer remember "<content>" [flags]               # add one episodic memory
dreamer remember-batch <file.jsonl>                # bulk-load memories
dreamer memories                                   # list stored memories
dreamer sleep [--cycles N] [--goals ...] ...       # run a night
dreamer reflect                                    # show last reflection
```

Every command accepts `--run <dir>` (default `runs/default`) and `--config <path>` (default: package YAML).

<details>
<summary><b>Full flag reference for <code>dreamer sleep</code></b></summary>

```
--run PATH            run directory (default: runs/default)
--config PATH         override the YAML config
--cycles N            override the number of NREM→REM cycles
--goals "a,b,c"       comma-separated current agent goals
--obstacles "a,b"     comma-separated known obstacles (used by lucid)
--competence "..."    one-line free-text skill description
```

</details>

## Testing

```bash
pytest -q                                # 12 tests, no network
ruff check dreamer tests                 # lint
```

The orchestrator test uses a `FakeProvider` that returns deterministic stub text (plus valid JSON for the reflection stage), so the whole night pipeline can be exercised with zero API calls and zero keys.

## Evaluation plan

Without downstream evaluation this is well-engineered theatre. With it, it becomes a falsifiable claim. The `dreamer/evaluation/` scaffold is where the A/B harness lives. Planned experiments:

- **Dream vs. flat replay** — same agent, N nights with dreaming vs. N nights with plain experience replay → task success on a held-out benchmark.
- **Ablations** — remove nightmares / reflection / N3 independently and measure the delta.
- **Transfer** — train on environment A, sleep, test on environment B. This is the actual generalization claim.
- **Dream quality** — LLM-as-judge on coherence × novelty × downstream utility.
- **Cost curve** — dollars per unit of improvement. When does dreaming beat just training longer on the raw episodic data?

PRs extending this harness are the highest-leverage contribution possible.

## Roadmap

- [x] Provider abstraction across Anthropic / Google / OpenAI / custom
- [x] Seven-stage sleep architecture with per-stage routing
- [x] Salience-weighted replay sampler
- [x] Nightmare difficulty controller (ZPD-targeted)
- [x] Structured morning reflection with safety gate
- [x] Skill manifests for Claude Code / Codex / OpenCode
- [ ] Vector-DB memory backend (Chroma / Qdrant / pgvector)
- [ ] LoRA training pipeline gated behind reflection plan
- [ ] Streaming output during REM (for live UIs)
- [ ] Dream timeline viewer (web UI)
- [ ] Multi-agent shared dreams (agents read each other's journals)
- [ ] Evaluation harness with preset benchmarks
- [ ] Continuous background dreaming during idle (not just batched)

## FAQ

<details>
<summary><b>Is the agent's underlying model actually being updated?</b></summary>

No — not in this POC. `llm-sleep` modifies a retrieval store (episodic + semantic memory). Weight-level consolidation via LoRA or fine-tuning on dream rollouts is a downstream pipeline, kept intentionally out of scope so the system is testable without GPUs. The `consolidation_plan.train_on` output is the hook for that.
</details>

<details>
<summary><b>Why is this different from "just prompt the LLM to reflect"?</b></summary>

Three things. First, salience-weighted replay picks *which* memories the model reflects on — you can't get this from a single prompt. Second, each stage has its own temperature and role, mirroring the entropy shift across real sleep cycles. Third, nightmares are targeted at the competence frontier with explicit difficulty control, which is closer to curriculum-learning RL than to journaling.
</details>

<details>
<summary><b>Can I use this with a local model?</b></summary>

Yes. Set `CUSTOM_BASE_URL=http://localhost:11434/v1` (or wherever your Ollama / LM Studio / vLLM server is) and `CUSTOM_API_KEY=ollama` (any non-empty string for servers that don't check it). Then use the `local` profile in `dreamer/profiles.yaml`.
</details>

<details>
<summary><b>Why JSONL instead of a real database?</b></summary>

Proof-of-concept ergonomics. The `MemoryStore` abstraction is where you'd swap in Chroma / Qdrant / pgvector. JSONL means you can `cat runs/demo/dreams.jsonl | jq` to inspect any run, which is hugely useful during prompt iteration.
</details>

<details>
<summary><b>Is this safe?</b></summary>

The safety gate refuses to auto-apply value or goal changes under any circumstance. Skill-level changes require human review. Nightmares are deliberately adversarial — if this is inappropriate for your use case, set `nightmare_enabled: false` in your config. The system does not call any tools, execute any code, or interact with the outside world beyond the LLM endpoints you configure.
</details>

<details>
<summary><b>How much does a night cost?</b></summary>

Depends entirely on routing. A 3-cycle night is 8–14 model calls:

- `cheap` profile (nano/flash-lite): **≈ $0.01**
- `default` profile (haiku + sonnet): **≈ $0.10**
- `frontier` profile (opus + gemini-3.1-pro): **≈ $0.50**
- `local` profile (self-hosted): **free**

Use `dreamer sleep --cycles 1` for dev loops to cut cost ~3×.
</details>

<details>
<summary><b>Can agents share dreams?</b></summary>

Not yet — it's on the roadmap. The `runs/<id>/` directory-per-agent structure is designed so cross-agent reads are trivial to add: point one agent's N1 sampler at another agent's `reflections.jsonl`.
</details>

## Citation

```bibtex
@software{llm_sleep_2026,
  author = {leofratu},
  title  = {llm-sleep: A dream emulator for AI agents},
  year   = {2026},
  url    = {https://github.com/leofratu/llm-sleep}
}
```

## Prior art

The shoulders this stands on:

- Ha & Schmidhuber — *World Models* (2018)
- Hafner et al. — *Dreamer V1–V3* (2020–2023)
- Schaul et al. — *Prioritized Experience Replay* (ICLR 2016)
- Stickgold & Walker — *Sleep-Dependent Memory Triage* (Nat. Neurosci., 2013)
- Tononi & Cirelli — *Sleep and the Price of Plasticity* (Neuron, 2014)
- Wagner et al. — *Sleep inspires insight* (Nature, 2004)
- Diekelmann & Born — *The memory function of sleep* (Nat. Rev. Neurosci., 2010)

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). High-leverage areas: evaluation harness, vector-DB backend, LoRA pipeline behind the safety gate, and more skill hosts.

## License

MIT. See [`LICENSE`](LICENSE).

---

<div align="center">
<sub>Built because the ingredients already exist in ML — they just weren't on the same table.</sub>
</div>
