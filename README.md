# claude-log

A lightweight, token-efficient session logging plugin for Claude Code. It
maintains an append-only, per-project log of session turns — one concise
summary per turn plus metadata (files touched, git commits) — so a session
can resume with just the recent context instead of full conversation
history.

## Problem It Solves

Existing session tracking tools waste tokens by sending full conversation
history at every turn or producing verbose, redundant summaries. claude-log
summarizes each turn once (user prompt + all of Claude's assistant messages
for that turn) and only ever feeds the last few log entries back in, not the
whole history.

## How It Works

1. **Install as a personal plugin** (see Installation) — hooks register
   once, for every project on the machine, no per-project setup.
2. Each turn's assistant messages are captured incrementally via
   `MessageDisplay` and buffered to disk, keyed by `<session_id>__<prompt_id>`
   so a crash or interrupt never corrupts another turn's buffer.
3. On `Stop`, the buffered turn (prompt + assistant messages) plus a
   git-snapshot diff of files touched during the turn are sent to a
   user-configured OpenAI-compatible summarization endpoint.
4. The summary is appended as one JSON line to
   `<project>/.claude-log/logs/<session_id>.jsonl`. If summarization fails
   for any reason, an honest `summary_failed` marker is written instead —
   **never** a fabricated or rule-based placeholder summary.
5. `/clear` gates how much of the log gets fed back into future
   summarization calls (growing back up to the configured window as new
   turns land); `/claude-log-load [count]` lets the user manually re-ingest
   recent entries after a clear. Resuming a session (`--resume` / picking
   up a prior session) is not gated — it gets the full configured window
   immediately.
6. Interrupted or crashed turns (no `Stop` fires on a `Ctrl+C` interrupt)
   are swept into `turn_lost` markers on the next `UserPromptSubmit` or on
   `SessionEnd`, so nothing silently vanishes from the log.

See `SPEC.md` and `docs/specs/core-logging.md` for the full design, and
`docs/adr/` for the reasoning behind each of these decisions.

## Installation

claude-log ships as a personal skills-directory plugin, not a per-project
hook registration — load it once and it applies to every project:

```
claude --plugin-dir /path/to/claude-log
```

(or add it to your persistent plugin configuration so it loads
automatically on every session).

## Configuration

Settings live at `~/.claude-log/config.json` (created with defaults on
first run if absent):

```json
{
  "enabled": true,
  "recent_context_window": 10,
  "summarization_endpoint": {
    "url": "http://localhost:8000/v1/chat/completions",
    "model": "your-model-name"
  },
  "log_level": "info"
}
```

`summarization_endpoint` must point at an OpenAI-compatible
`/v1/chat/completions` endpoint (local or remote). If it's left `null`,
every turn logs a `summary_failed` marker — there is no rule-based
fallback, by design (see `docs/adr/0002`).

## Where Things Live

- `~/.claude-log/config.json` — user settings (this machine, all projects).
- `~/.claude-log/internal.log` — claude-log's own rotating operational log
  (for debugging the plugin itself), level controlled by `log_level`.
- `<project>/.claude-log/logs/<session_id>.jsonl` — the actual session
  logs, one file per session, per project.
- `<project>/.claude-log/.buffers/`, `<project>/.claude-log/.state/` —
  transient, disposable working files (per-turn buffers, context-reset
  bookkeeping). Safe to delete; claude-log recreates them as needed.

Since `<project>/.claude-log/` lives inside the project directory, add it
to that project's `.gitignore` unless you intend to version your session
logs — otherwise claude-log's own writes (e.g. its `.state/` file) will
show up as "files touched" on whatever turn happens to trigger them, since
they're genuinely part of the working tree's diff at that point.

## Status

Core Logging is implemented and has passed a full real-world end-to-end
test (headless sessions, `--resume`, `/clear`, `/compact`,
`/claude-log-load`, an interrupted turn, and git-snapshot file tracking
across multi-commit turns and untracked directories). See `CHANGELOG.md`
for release history and `BACKLOG.md` for known limitations and deferred
work.

## Contributing

See `~/.claude/CLAUDE.md` for project conventions and workflow (this
project follows the user-level conventions, not a project-local copy).
