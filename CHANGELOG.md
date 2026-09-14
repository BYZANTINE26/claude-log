# Changelog

All notable changes to claude-log are documented here, following
[Keep a Changelog](https://keepachangelog.com/) format.

## [0.1.0] - 2026-09-13

### Added
- Core Logging: personal Claude Code plugin that appends one summarized
  entry per session turn to `<project>/.claude-log/logs/<session_id>.jsonl`.
- Five-hook lifecycle (`SessionStart`, `UserPromptSubmit`, `MessageDisplay`,
  `Stop`, `SessionEnd`) capturing the full turn (user prompt + all of
  Claude's assistant messages, not just the final one).
- Git-snapshot-diff file tracking (`claude_log/git_snapshot.py`): commit
  hash pairs plus content-hashed dirty-file sets, correctly handling
  multi-commit turns, branch switches, pre-existing dirty files, deletions,
  and untracked files.
- OpenAI-compatible `/v1/chat/completions` summarization client
  (`claude_log/summarizer.py`), configurable via `~/.claude-log/config.json`.
  No rule-based fallback: any failure writes an honest `summary_failed`
  marker, never a fabricated summary.
- `prompt_id`-keyed, disposable per-turn buffers
  (`<session_id>__<prompt_id>.json`) with an orphan sweep on every
  `UserPromptSubmit` and unconditionally on `SessionEnd`, producing
  `turn_lost` markers for interrupted or crashed turns (`Stop` does not
  fire on a `Ctrl+C` interrupt).
- Context-reset window: `/clear` marks a reset that gates how much of the
  log feeds back into future summarization calls, growing back toward the
  configured window as new turns land; a `--resume`d session is not gated
  and gets the full window immediately.
- `/claude-log-load [count]` skill for manually re-ingesting recent log
  entries after a `/clear`.
- Rotating internal operational log at `~/.claude-log/internal.log`, level
  configurable via `log_level`.

### Fixed
- `git_snapshot.py::_hash_paths` silently emptied the entire dirty-file
  hash map for a turn whenever the working tree contained any wholly
  untracked directory (found live during real end-to-end testing, triggered
  by claude-log's own `.claude-log/.state/` directory). `git status
  --porcelain` folds an untracked directory into a single unhashable line,
  and the batched `git hash-object` call over all dirty paths fails outright
  on it — silently discarding every other file's hash too, not just that
  one path's. Fixed by adding `--untracked-files=all` to the status call
  (forces individual file listing) plus an `os.path.isfile` filter before
  hashing (defense in depth for submodule-like paths). Verified fixed by a
  fresh, independent end-to-end re-test (new untracked directory with
  multiple files alongside an unrelated tracked-file edit in the same
  turn — all files now correctly reported).

## [0.2.1] - 2026-09-14

### Fixed
- `/claude-log-load [count]` was re-ingesting each entry's full JSON
  (`turn_id`, `timestamp`, and the entire `refs` block — commit hashes,
  touched files) into the model's context window, not just the 1–2 line
  summary the design calls for. `claude_log/cli.py:load_recent` now
  prints a plain numbered list of summaries only; the audit metadata
  stays in the log file for humans reading it directly, never
  re-ingested.

## [0.2.0] - 2026-09-13

### Added
- `LICENSE` (MIT) and public-listing metadata (`repository`, `homepage`,
  `license`, `keywords`) in `.claude-plugin/plugin.json`.
- `.claude-plugin/marketplace.json` — claude-log is now installable
  through Claude Code's own mechanism (`claude plugin marketplace add`
  + `claude plugin install`), not just `--plugin-dir` or manual
  skills-directory cloning. Verified with a real install/uninstall test.
- A second, independent `summarization_endpoint` provider,
  `"provider": "claude-code"` — summarize turns through the user's
  existing Claude Code login instead of a separate OpenAI-compatible
  server. Any Claude model id, extended thinking disabled
  (`MAX_THINKING_TOKENS=0`), and hooks/plugins/MCP/tools all disabled
  for the subprocess (`--safe-mode --tools ""`) so it can't re-trigger
  claude-log's own hooks or take any action — confirmed recursion-free
  with a live spike before implementation, not just assumed.
- Advisory OS-level file locking (`fcntl` on POSIX, `msvcrt` on Windows)
  around the session log and `.state` file writes, so two Claude Code
  sessions sharing a `session_id` can no longer interleave writes or
  lose an update.

### Changed
- `hooks/hooks.json` switched from shell-form hook commands to exec
  form (`command`/`args`), for portability — shell form relied on the
  `#!/usr/bin/env python3` shebang and the executable bit, which is
  fragile on Windows.
- `README.md` rewritten for a first-time plugin installer: a real
  marketplace-install quickstart, a plain-language "what does this do
  to my machine" section, first-run troubleshooting, both
  `summarization_endpoint` shapes documented side by side, and a
  License section.

### Known limitations
- `python3` must be on `PATH`; on Windows this isn't guaranteed by a
  standard python.org install (only `python.exe`/`py.exe`) and hasn't
  been verified on a real Windows machine.
- The full unit suite passes on real Linux (Docker) in addition to
  macOS; Windows remains genuinely untested.
