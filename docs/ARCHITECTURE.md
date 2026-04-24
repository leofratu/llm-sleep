# Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                           dreamer.cli                             │
│  typer-based CLI (remember / memories / sleep / reflect / …)      │
└──────────────────────────────┬────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────┐
│                       orchestrator.scheduler                      │
│                                                                   │
│  run_night(cfg, providers, store, agent_state):                   │
│    for cycle in cfg.num_cycles:                                   │
│       N1 → N2 → N3 → REM → (nightmare?) → (lucid on last cycle)   │
│    reflection  (morning)                                          │
└───┬──────────────────────┬─────────────────────────┬──────────────┘
    │                      │                         │
    ▼                      ▼                         ▼
┌─────────────┐   ┌──────────────────┐   ┌────────────────────────┐
│   memory    │   │     stages       │   │      providers         │
│             │   │                  │   │                        │
│  store      │   │  runner          │   │  base (Protocol)       │
│  salience   │   │  prompts         │   │  anthropic             │
│             │   │                  │   │  google (OpenAI-compat)│
│             │   │                  │   │  openai                │
│             │   │                  │   │  custom (any OpenAI-   │
│             │   │                  │   │         compat URL)    │
└─────────────┘   └──────────────────┘   └────────────────────────┘
    │                                              │
    └──► JSONL files under runs/<id>/              └──► HTTPS
```

## Module responsibilities

### `dreamer.config`
Single source of truth for the night schedule, per-stage sampling
parameters, per-stage provider routing, salience weights, nightmare
controller targets, and consolidation safety flags.

### `dreamer.providers`
A uniform `DreamProvider` protocol. Four concrete impls. All chat-like
providers reuse one OpenAI-compatible HTTP helper so adding another
endpoint (Groq, Together, OpenRouter, vLLM, Ollama, ...) is a two-line
class.

### `dreamer.memory`
JSONL-backed episodic + semantic store (deliberately simple for the POC;
the module boundary is right for swapping in Chroma/Qdrant/pgvector).
Plus the salience scorer that drives which memories get replayed.

### `dreamer.stages`
A single `run_stage` function looks up the stage's prompt template and
provider route, makes the call, and records the result as a
`DreamRecord`. All stage-specific logic lives in `prompts.py`.

### `dreamer.orchestrator`
The scheduler — converts `num_cycles` into a linear sequence of stage
calls, decides when nightmares fire (unresolved negative affect) and
when lucid dreams fire (last cycle), then triggers the morning
reflection.

### `dreamer.consolidation`
The safety gate. Auto-applies facts; flags skill-level updates for
review; *never* auto-applies value/goal changes.

## Extension points

| Want to …                          | Edit                                       |
|------------------------------------|--------------------------------------------|
| Add a new provider                 | New module in `providers/` + register in `providers/__init__.py` |
| Add a new sleep stage              | Prompt in `stages/prompts.py` + wire in `orchestrator/scheduler.py` |
| Change the salience function       | `memory/salience.py`                       |
| Swap JSONL for a vector DB         | Reimplement `MemoryStore`, same interface  |
| Add actual LoRA training           | `consolidation/` + gate in `gate.py`       |
| Add evaluation harness             | `evaluation/` (empty scaffold present)     |

## Design notes

- **Everything is async** through to the HTTP layer; stages run
  sequentially within a cycle (they depend on each other) but cycles
  *could* parallelize in future.
- **Nothing imports a specific provider** — everything flows through
  `build_providers(cfg)` → dict → `DreamProvider` protocol. This is
  what makes stage-per-vendor routing cheap.
- **Prompts are data, not code**. They live in one file so prompt
  iteration doesn't require touching orchestration.
- **Reflection is the only schema-critical stage**. All others return
  prose which the orchestrator passes forward verbatim. The reflection
  parser is deliberately forgiving (code-fence stripping, widest-braces
  fallback, `_parse_error` sentinel if all else fails).
