# Backlog

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

## Publish

Findings from a 2026-09-13 gap analysis (grounded in `plugins.md`,
`plugin-marketplaces.md`, `plugins-reference.md`, and `hooks.md`, fetched
directly rather than assumed) on what's required to ship claude-log as a
plugin anyone can install through Claude Code, not just load locally via
`--plugin-dir` or hand-clone into `~/.claude/skills/`.

- **[technical-debt] #17** No real Windows verification exists. The full
  unit suite (65 tests) now passes on real Linux too (Docker,
  `python:3.12-slim`, 2026-09-13) — genuine evidence for the `fcntl`-based
  file locking (`#16`), git subprocess calls, and path handling on a
  different kernel/filesystem, not just macOS. The `claude` CLI installs
  cleanly in a Linux container as well, but a real headless run there
  would need personal auth credentials placed in a throwaway container,
  which wasn't done. Windows remains genuinely untested — no Windows
  container path was available, and `#15`'s exec-form fix plus the
  `python3`-vs-`python` prerequisite are still unverified for real there.
  Parked 2026-09-13, narrowed from "no cross-platform testing at all" to
  "Windows specifically."

- **[research]** Tickets `#10` (unreproduced `files: []` anomaly) and
  `#11` (queued-prompt sequencing) are low-stakes for a single careful
  user but more likely to surface as confusing bug reports once install
  numbers go up. Not necessarily blocking for an initial 0.x public
  release, but worth another look before declaring a stable 1.0. No new
  ticket number — cross-referencing the existing entries above.

- **[good-to-have] #21** Submit claude-log to the public `claude-community`
  marketplace (via the in-app forms at claude.ai or platform.claude.com),
  so users don't need to add `BYZANTINE26/claude-log` as a custom
  marketplace themselves first. Split out from the original marketplace-
  distribution ticket, which is otherwise resolved —
  `.claude-plugin/marketplace.json` exists and a real `claude plugin
  marketplace add` + `claude plugin install` test passed. Submission runs
  `claude plugin validate` plus automated safety screening, and only
  makes sense once the real plugin content lands on `main` — the
  marketplace entry's `source` has no `ref`, so it resolves to whatever
  the repo's default branch is at install time. Parked 2026-09-13, not
  started.
