# Branch: feature/core-logging

## Purpose
Implement claude-log's Core Logging as designed in the `grill-with-docs`
redo: `INTENT.md`, `SPEC.md`, `docs/specs/core-logging.md`, `docs/adr/
0001`-`0007`, and `.claude/plans/PLAN.md`. This replaces the scrapped
`feature/core-logging-mvp` branch's implementation entirely — nothing
from it is reused as-is.

## Goal
A working personal Claude Code plugin that:
- Logs one entry per turn to `<project>/.claude-log/logs/<session_id>.jsonl`,
  using `prompt_id` as `turn_id`
- Captures a turn's prompt + all assistant messages (no per-tool-call
  tracking) and derives touched files from a git-snapshot diff
- Calls an OpenAI-compatible summarization endpoint, with explicit
  `summary_failed`/`turn_lost` marker entries on any failure — never a
  fabricated summary or a silent gap
- Handles session lifecycle: resume, `/clear` context-reset boundary,
  `/claude-log-load [count]` manual re-ingestion, and a `SessionEnd`
  orphan sweep

## Explicitly out of scope for this branch
- Real local summarization model setup guidance (the HTTP contract is
  final; "which model to run" stays a `BACKLOG.md` item)
- Benchmarking suite vs. claude-mem
- Everything else currently in `BACKLOG.md`

This file is unique to this branch, never merged into `dev`.
