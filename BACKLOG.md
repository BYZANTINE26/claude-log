# Backlog

Tickets parked for later. Each entry: flag, one-line summary, and where/when
it was parked.

## technical-debt
- Mid-session crash (Stop hook never fires) leaves stale turn-buffer data
  that silently merges into the next turn's summary. Parked during Core
  Logging MVP planning (2026-09-11) — accepted as an MVP limitation, see
  `.claude/plans/PLAN.md`.
- No file locking on the session log; two sessions sharing a `session_id`
  would corrupt it (single-writer assumption, unhandled). Parked during Core
  Logging MVP planning (2026-09-11).
- No log rotation or retention policy — session logs grow unbounded. Parked
  during Core Logging MVP planning (2026-09-11).

## feature
- Real local summarization endpoint integration (e.g. Ollama) to replace the
  rule-based stub summarizer. Parked during Core Logging MVP planning
  (2026-09-11) — stub is deliberate for MVP, see `.claude/plans/PLAN.md`.
- Benchmarking suite comparing claude-log vs. claude-mem on token usage,
  context fidelity, and resumability. This is an INTENT.md success
  criterion, tracked as its own phase after the MVP — not blocking it.
  Parked during Core Logging MVP planning (2026-09-11).

## good-to-have
- Viewing/querying UI or CLI for browsing a session log. Parked during Core
  Logging MVP planning (2026-09-11).
- Export a session log to markdown/CSV; search/filter across multiple
  session logs. Parked during Core Logging MVP planning (2026-09-11).
- Compression/encryption for archived log files. Parked during Core Logging
  MVP planning (2026-09-11).
