# Backlog

- **[technical-debt] #1** No file locking on the session log — two Claude Code
  sessions sharing a `session_id` would corrupt `<project>/.claude-log/logs/
  <session_id>.jsonl` since writes aren't coordinated across processes. Parked
  2026-09-11 during the Core Logging MVP's first planning pass; single-writer
  is an accepted assumption for now (see `docs/specs/core-logging.md`).

- **[technical-debt] #2** No rotation or retention policy on the per-session
  summarized logs (`<project>/.claude-log/logs/<session_id>.jsonl`,
  `claude_log/logger.py::append_entry`) — they grow unbounded for the life
  of a session. Not to be confused with `~/.claude-log/internal.log`, the
  plugin's own operational log, which already rotates
  (`claude_log/config.py::get_logger`'s `RotatingFileHandler`). Parked
  2026-09-11.

- **[technical-debt] #3** `refs.commit_before`/`commit_after` become dangling
  references if the commit is later amended, rebased, or reset — the stored
  hash no longer resolves to anything in `git log`. Parked 2026-09-13 during
  the grill-with-docs redo (`docs/adr/0004-drop-rich-mode-and-tool-call-tracking.md`);
  accepted as the same class of limitation as any commit-hash-based audit
  trail.

- **[enhancement] #4** `get_recent_entries` re-reads the whole JSONL log file
  every turn to compute the tail slice — fine at MVP scale, but should switch
  to a seek-from-end read once logs grow large enough for this to matter.
  Parked 2026-09-13, `docs/specs/core-logging.md`.

- **[feature] #5** Real local summarization model behind the OpenAI-compatible
  `/v1/chat/completions` contract (see `SPEC.md`'s Integration Points and the
  reference request shape in `docs/specs/core-logging.md`) — the HTTP client
  is real, only "which model to run" is deferred to the user's own setup.
  Parked 2026-09-11.

- **[feature] #6** Benchmarking suite comparing claude-log vs. claude-mem on
  token usage, context fidelity, and resumability — its own phase post-MVP,
  tracked as an `INTENT.md` success criterion, not blocking Core Logging.
  Parked 2026-09-11.

- **[good-to-have] #7** Viewing/querying UI or CLI for browsing a session log.
  Parked 2026-09-11.

- **[good-to-have] #8** Export a session log to markdown/CSV; search/filter
  across multiple session logs in a project. Parked 2026-09-11.

- **[good-to-have] #9** Compression/encryption for archived log files. Parked
  2026-09-11.

- **[research] #10** A real end-to-end test run (subagent, `--plugin-dir` +
  a throwaway test project, `/Volumes/GBC/projects/test_claude_log`) hit
  one `files: []` result on a genuine edit-only turn (editing an already-
  created `hello.txt`) that could not be reproduced in 3 follow-up
  attempts of the same create-then-edit sequence, and predates the
  separately-found-and-fixed untracked-directory bug
  (`claude_log/git_snapshot.py::_hash_paths`, see CHANGELOG). Recorded
  as an unexplained one-off, not a confirmed bug — revisit if it recurs
  with a reproducible trigger. Parked 2026-09-13. A second independent
  re-test on 2026-09-13 (fresh throwaway project
  `/Volumes/GBC/projects/test_claude_log_v2`, 5 repeated create-then-edit
  attempts) also failed to reproduce it — still unexplained, still not
  blocking, ticket stays open in case it recurs with a real trigger.

- **[research] #11** How a prompt queued before the prior turn's `Stop` fires
  sequences against that turn's `prompt_id` is still undocumented (whether
  `UserPromptSubmit` for the queued prompt can fire before the earlier
  turn's `Stop`). Confirmed separately, directly from the hooks reference's
  own Stop section: `Stop` does **not** fire on a Ctrl+C interrupt at all
  (API errors go to `StopFailure` instead), so the interrupt case is no
  longer a research item — `docs/adr/0006-prompt-id-keyed-turn-buffers.md`'s
  `turn_lost` orphan sweep is confirmed necessary, not hypothetical.
  Partially exercised 2026-09-13 in the real end-to-end test run: two
  `--resume <same session_id>` invocations launched back-to-back showed
  no corruption or interleaving at the JSONL or buffer-file level, each
  getting its own correctly-separated buffer and log entry — but this is
  concurrent headless resumes, not confirmed proof of the interactive
  "prompt queued while the model is still generating" scenario the
  question is actually about. Parked 2026-09-13, still open.

- **[enhancement] #12** `~/.claude-log/internal.log`'s `debug`/`info` levels are
  currently dead weight — `claude_log/config.py::get_logger`'s level
  filtering and rotating handler work correctly, but no code path calls
  `logger.debug(...)` or `logger.info(...)` anywhere; only `warning`
  (`summarizer.py`: no endpoint configured) and `error` (each hook's
  caught-exception handler, `summarizer.py`'s failed endpoint call) are
  ever logged. Found 2026-09-13 while reviewing why the independent
  post-fix re-test's `internal.log` had zero new lines despite
  `log_level: "debug"` being set — expected, since the re-test hit no
  failures, but it means `debug`/`info` currently show nothing even when
  set. If pursued: log each hook's entry/key decision (buffer started,
  git snapshot taken, summarization call made) at `debug`, successful
  turn completion at `info`, so the level setting is actually meaningful.
  Parked 2026-09-13, not blocking — the log's original purpose (crash/
  failure diagnostics) is unaffected.
