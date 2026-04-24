# llm-sleep — Codex / OpenAI Agent Instructions

This `AGENTS.md` teaches a Codex-style agent how to operate the
`llm-sleep` dream emulator as a tool.

## Tool summary

`llm-sleep` is a CLI (`dreamer`) that runs biologically-inspired offline
processing over an AI agent's episodic memories. It produces a morning
consolidation plan as JSON.

## Commands the agent should know

| Intent                                | Command |
|---------------------------------------|---------|
| Which providers are live?             | `dreamer providers` |
| Record a single memory                | `dreamer remember "<content>" --reward <f> --valence <f> --arousal <f> --tags "a,b" --run runs/<id>` |
| Bulk-load memories from JSONL         | `dreamer remember-batch <file> --run runs/<id>` |
| List stored memories                  | `dreamer memories --run runs/<id>` |
| Run a night                           | `dreamer sleep --run runs/<id> --cycles <n> --goals "..." --obstacles "..." --competence "..."` |
| Show most recent reflection           | `dreamer reflect --run runs/<id>` |

## Decision rules

1. **Before any `sleep` call**, verify `dreamer providers` shows at
   least one ready provider. If none, surface the missing env var to
   the user and stop.
2. **Use `--cycles 1`** for dev loops and demos. Full runs use 3–5.
3. **Pick a profile** via `--config`:
   - `cheap` for anything experimental.
   - `frontier` only when the user explicitly asks for "best".
   - `local` when the user doesn't want external API traffic.
4. **Never apply value-level changes** from the reflection automatically.
   The `consolidation_plan.value_changes` list must be surfaced to the
   user with the exact phrasing "requires human review".
5. **Preserve run directories**. One agent = one `runs/<id>` directory;
   don't mix agents' memories.

## Input format for `remember-batch`

JSONL, one `EpisodicMemory` per line:

```json
{"content": "<what happened>", "reward": 0.8, "expected_reward": 0.4,
 "valence": 0.7, "arousal": 0.5, "tags": ["a","b"]}
```

Fields:

- `reward` / `expected_reward`: surprise drives replay priority.
- `valence` ∈ [-1, 1]: sign = good/bad, magnitude = intensity.
- `arousal` ∈ [0, 1]: emotional energy.
- `tags`: free-form labels for later analysis.

## Output contract

The reflection JSON shape is:

```json
{
  "themes": ["..."],
  "insights": ["..."],
  "contradictions": ["..."],
  "skill_gaps": ["..."],
  "consolidation_plan": {
    "keep":     ["<id>"],
    "compress": [{"ids": ["<id>"], "into": "<fact>"}],
    "forget":   ["<id>"],
    "train_on": [{"dream_id": "...", "weight": 0.0}],
    "value_changes": ["..."]
  },
  "next_night_hints": ["..."],
  "affect_delta": {"valence": 0.0, "arousal": 0.0}
}
```

Use `next_night_hints` to inform tomorrow's goals.

## Failure modes to handle

- **HTTP 4xx from a provider**: surface the provider + status code to
  the user. Don't silently retry on 401.
- **Empty memory store**: the CLI will still run but dreams will be
  shallow. Warn the user.
- **JSON parse failure on reflection**: the raw text is preserved under
  `_raw` in the parsed reflection — forward it unchanged.
