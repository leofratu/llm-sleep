# Skills

Ready-to-install skill manifests that let coding agents drive
`llm-sleep` as a tool.

| Agent         | File                               | How to install |
|---------------|------------------------------------|----------------|
| Claude Code   | [`claude-code/SKILL.md`](claude-code/SKILL.md) | Copy into `~/.claude/skills/llm-sleep/SKILL.md` or project `.claude/skills/` |
| Codex CLI     | [`codex/AGENTS.md`](codex/AGENTS.md)           | Place at repo root or merge into an existing `AGENTS.md` |
| OpenCode      | [`opencode/skill.md`](opencode/skill.md)       | Copy into `~/.config/opencode/skills/llm-sleep/skill.md` |

## Why ship these

Every agent that reads one of these manifests will know:

- **When to invoke the dream emulator** (trigger phrases listed).
- **What commands to run** for each operation.
- **What the output schema looks like** and how to surface it.
- **Which plans never auto-apply** (value/goal changes require human review).

## Prerequisites (all agents)

```bash
pip install -e <path-to-llm-sleep>
dreamer providers      # must show at least one ready provider
```

See the top-level [`../README.md`](../README.md) for env var setup.

## Adding a new host

All three manifests follow the same shape — a frontmatter/header with
triggers, a "how to invoke" section with exact shell commands, and an
"output contract" section. Copy any of them and adapt the frontmatter
to your agent's skill format.
