# Backlog

- **[technical-debt]** No file locking on the session log — two Claude Code
  sessions sharing a `session_id` would corrupt `<project>/.claude-log/logs/
  <session_id>.jsonl` since writes aren't coordinated across processes. Parked
  2026-09-11 during the Core Logging MVP's first planning pass; single-writer
  is an accepted assumption for now (see `docs/specs/core-logging.md`).

- **[technical-debt]** No log rotation or retention policy — session logs grow
  unbounded for the life of a project. Parked 2026-09-11.

- **[technical-debt]** `refs.commit_before`/`commit_after` become dangling
  references if the commit is later amended, rebased, or reset — the stored
  hash no longer resolves to anything in `git log`. Parked 2026-09-13 during
  the grill-with-docs redo (`docs/adr/0004-drop-rich-mode-and-tool-call-tracking.md`);
  accepted as the same class of limitation as any commit-hash-based audit
  trail.

- **[enhancement]** `get_recent_entries` re-reads the whole JSONL log file
  every turn to compute the tail slice — fine at MVP scale, but should switch
  to a seek-from-end read once logs grow large enough for this to matter.
  Parked 2026-09-13, `docs/specs/core-logging.md`.

- **[feature]** Real local summarization model behind the OpenAI-compatible
  `/v1/chat/completions` contract (see `SPEC.md`'s Integration Points and the
  reference request shape in `docs/specs/core-logging.md`) — the HTTP client
  is real, only "which model to run" is deferred to the user's own setup.
  Parked 2026-09-11.

- **[feature]** Benchmarking suite comparing claude-log vs. claude-mem on
  token usage, context fidelity, and resumability — its own phase post-MVP,
  tracked as an `INTENT.md` success criterion, not blocking Core Logging.
  Parked 2026-09-11.

- **[feature]** Manual command for the user to ingest a configurable last-K
  log entries into a fresh (post-`/clear`) context window — settled as the
  `/claude-log-load [count]` skill in `docs/adr/0007-session-lifecycle-and-context-reset-window.md`,
  not yet implemented. Parked 2026-09-11.

- **[good-to-have]** Viewing/querying UI or CLI for browsing a session log.
  Parked 2026-09-11.

- **[good-to-have]** Export a session log to markdown/CSV; search/filter
  across multiple session logs in a project. Parked 2026-09-11.

- **[good-to-have]** Compression/encryption for archived log files. Parked
  2026-09-11.

- **[research]** Confirm empirically whether `Stop` fires on a Ctrl+C
  interrupt mid-generation, and how a prompt queued before the prior turn's
  `Stop` fires sequences against that turn's `prompt_id` — undocumented in
  Claude Code's hooks reference as of 2026-09-13. Current design
  (`docs/adr/0006-prompt-id-keyed-turn-buffers.md`) is safe either way —
  orphaned buffers always surface as `turn_lost` markers — but the actual
  behavior is unverified live. Parked 2026-09-13, verify during the Core
  Logging manual smoke test (`.claude/plans/PLAN.md`).
