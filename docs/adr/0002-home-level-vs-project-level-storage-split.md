---
Status: accepted
---

# Split storage: home-level plugin state vs. project-level session logs

Now that claude-log ships as a personal plugin (ADR-0001), its own
configuration and internal operational log are machine/user-scoped, not
project-scoped, so they live at `~/.claude-log/config.json` and
`~/.claude-log/internal.log` — decoupled from both Claude Code's own
`~/.claude/` tree and any single project. Session summaries, by
contrast, are what the project's contributors actually want to read
alongside their code, so they stay project-scoped at
`<project_root>/.claude-log/logs/<session_id>.jsonl`.

## Considered Options
- Everything under `~/.claude-log/`, keyed by project path — keeps one
  location, but session logs stop traveling with the project (can't be
  committed, reviewed in a PR diff, or found by someone else cloning the
  repo).
- Everything under `<project>/.claude-log/` — puts machine-specific
  plugin config inside a shared, potentially-committed project tree.

## Consequences
A future reader must know to look in two places: `~/.claude-log/` for
"is claude-log configured/working" questions, `<project>/.claude-log/`
for "what happened in this session" questions.
