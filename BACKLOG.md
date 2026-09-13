# Backlog

Tickets parked for later. Each entry is one line: a summary plus when it
was parked, grouped under its flag.

## technical-debt
- No file locking on the session log; concurrent writers sharing a
  `session_id` would corrupt it. Parked 2026-09-11.
- No log rotation or retention policy — session logs grow unbounded.
  Parked 2026-09-11.
- `commit_before`/`commit_after` become dangling refs if amended,
  rebased, or reset after being logged. Parked 2026-09-13.

## enhancement
- `get_recent_entries` re-reads the whole JSONL file every turn; fine at
  MVP scale, switch to a seek-from-end read if logs grow large. Parked
  2026-09-13.

## feature
- Real local summarization model behind the OpenAI-compatible endpoint
  contract, to replace/complement the rule-based fallback. Parked
  2026-09-11.
- Benchmarking suite vs. claude-mem on token usage, context fidelity, and
  resumability — its own phase post-MVP (INTENT.md success criterion).
  Parked 2026-09-11.
- Manual command for the user to ingest a configurable last-K log entries
  into a fresh (post-`/clear`) context window. Parked 2026-09-11.

## good-to-have
- Viewing/querying UI or CLI for browsing a session log. Parked
  2026-09-11.
- Export a session log to markdown/CSV; search/filter across multiple
  session logs. Parked 2026-09-11.
- Compression/encryption for archived log files. Parked 2026-09-11.

## research
- Confirm empirically whether `Stop` fires on a Ctrl+C interrupt, and how
  a prompt queued mid-generation sequences against the prior turn's
  `prompt_id` — undocumented; current design (orphaned buffers surface as
  `turn_lost` markers) is safe either way but unverified live. Parked
  2026-09-13.
