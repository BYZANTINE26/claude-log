# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.0] - 2026-09-11

### Added
- `INTENT.md`, `SPEC.md`, and `docs/specs/core-logging.md` establishing
  claude-log's problem statement, architecture, and component design: a
  lightweight, append-only, per-session JSONL log that summarizes each
  turn in 1-2 lines using only recent log context, instead of resending
  full conversation history.
- `claude_log/` Python package implementing the Core Logging MVP:
  `config.py` and `paths.py` for settings and path resolution;
  `buffer.py` for atomic per-turn scratch state (a turn's prompt and tool
  calls are accumulated across separate hook process invocations, since
  Claude Code hooks share no memory); `logger.py` for the append-only
  JSONL log and resumability; `summarizer.py` with a pluggable HTTP
  endpoint contract backed by a rule-based fallback heuristic;
  `metadata.py` for git commit hash and touched-files extraction.
- Four Claude Code hooks (`SessionStart`, `UserPromptSubmit`,
  `PostToolUse`, `Stop`) registered in `.claude/settings.json`, batching
  each turn into exactly one log entry at `Stop` rather than logging
  every individual event.
- `.claude/claude_log_config.json` for claude-log's own configuration
  (verbosity, recent-context window, summarization endpoint, log
  directory), kept separate from Claude Code's own `settings.json` whose
  schema rejects unrecognized top-level keys.
- Test suite of 37 tests (`tests/`) covering buffer atomicity, JSONL log
  correctness, summarizer fallback behavior, metadata extraction, and
  full hook-to-hook turn sequences fed via canned stdin fixtures.
- `BACKLOG.md` tracking deferred items: mid-turn crash recovery, log
  locking/rotation, real local-model summarization, the benchmarking
  suite against claude-mem, and viewing/export tooling.

### Fixed
- `post_tool_use.py` originally serialized the entire `tool_response`
  dict (which for Edit/Write tools contains the full old/new file
  content) into the turn buffer via `str()`. Caught live when this
  project's own hooks fired during its own implementation session;
  replaced with a short descriptor (response type + file path) so the
  buffer never carries full diff content — the exact token bloat this
  project exists to avoid.
