# Branch: bug/reingest-summaries-only

## Purpose

`/claude-log-load [count]` (`claude_log/cli.py:load_recent`) currently
re-ingests each log entry's **full JSON** — `turn_id`, `timestamp`,
`summary`, and the entire `refs` block (`commit_before`, `commit_after`,
`files`) — into the model's context window on reload. That contradicts
the project's own design intent (`SPEC.md`, README): only the 1–2 line
summaries should be fed back, not the audit metadata. `refs` exists for
a human reading the log file directly, not for re-ingestion.

## Scope

- Fix `load_recent` to print just the summary text per entry (numbered
  list, same convention `summarizer._build_user_content` already uses:
  `f"{index + 1}. {entry.get('summary', '[no summary]')}"`), dropping
  `turn_id`/`timestamp`/`refs` from what's printed.
- Update `skills/claude-log-load/SKILL.md`'s doc comment, which
  currently says "one JSON object per line — each is a prior turn's
  summary and metadata."
- Update `tests/test_cli.py` to assert the new plain-text format instead
  of JSON lines.

Out of scope: the `record_reingestion`/window-growth logic itself, which
is unaffected — only what gets *printed* changes.
</content>
