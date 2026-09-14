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
   summarization endpoint — either your own OpenAI-compatible server, or
   your existing Claude Code login (see Configuration).
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

## What This Does to Your Machine

Once installed, claude-log runs automatically for **every project** you
open Claude Code in — there's no per-project opt-in. Concretely, it:

- Writes a small amount of data on every turn: one JSON line per turn to
  `<project>/.claude-log/logs/<session_id>.jsonl`, plus transient files
  under `<project>/.claude-log/.buffers/` and `.state/` (cleaned up as
  part of normal operation).
- Reads your project's git state (`git status`, `git diff --name-only`,
  `git hash-object`) to figure out which files a turn touched — it never
  runs `git commit`, `git push`, or anything that changes your repo.
- If you configure a summarization endpoint, sends the turn's prompt and
  assistant messages to it (either your own server, or a `claude -p`
  subprocess using your existing login — see Configuration). If you
  don't configure one, nothing leaves your machine; every turn just logs
  a `summary_failed` marker.
- Keeps its own settings and operational log at `~/.claude-log/` (see
  Where Things Live), separate from any project.

It never reads or sends your actual file contents anywhere except your
own configured summarization endpoint (or your own Claude Code login),
and never modifies files in your project.

## Installation

### Prerequisite

Every hook is a Python script, invoked as `python3 <script path>`
(exec form, for portability — see `hooks/hooks.json`). **`python3`
(3.10+) must be on `PATH`.** On macOS and Linux this is almost always
already true. On Windows, a standard python.org install only adds
`python.exe`/`py.exe` to `PATH`, not `python3.exe` — you'll need to
either add a `python3` alias/shim yourself, or install Python through a
distribution that provides one (e.g. the Microsoft Store package, or
WSL). This hasn't been tested on a real Windows machine; if hooks
silently fail to run there, this is the first thing to check.

### Install through Claude Code (recommended)

claude-log ships as a real Claude Code plugin, distributed through its
own marketplace file (`.claude-plugin/marketplace.json`) in this repo:

```
claude plugin marketplace add BYZANTINE26/claude-log
claude plugin install claude-log@claude-log
```

That's it — no per-project setup, hooks apply to every project on the
machine from then on.

### Alternative: load without installing

For trying it out or developing on it, load it directly for a single
session, without registering a marketplace:

```
claude --plugin-dir /path/to/claude-log
```

## Configuration

Settings live at `~/.claude-log/config.json` (created with defaults on
first run if absent):

```json
{
  "enabled": true,
  "recent_context_window": 10,
  "summarization_endpoint": null,
  "log_level": "info"
}
```

| Key | Default | Meaning |
|---|---|---|
| `enabled` | `true` | Turn claude-log off entirely (every hook becomes a no-op) without uninstalling it. |
| `recent_context_window` | `10` | How many past log entries feed into each summarization call. |
| `summarization_endpoint` | `null` | See below. `null` means every turn logs an honest `summary_failed` marker — there is no rule-based fallback, by design (see `docs/adr/0003`). |
| `log_level` | `"info"` | `debug`/`info`/`warning`/`error` for `~/.claude-log/internal.log`. |

`summarization_endpoint` has two independent shapes — pick one:

**Your own OpenAI-compatible server** (local model, or any provider
speaking the `/v1/chat/completions` contract):

```json
{
  "summarization_endpoint": {
    "url": "http://localhost:8000/v1/chat/completions",
    "model": "your-model-name",
    "api_key": "optional-bearer-token",
    "timeout_seconds": 30
  }
}
```

**Through your existing Claude Code login** — no separate server, API
key, or account:

```json
{
  "summarization_endpoint": {
    "provider": "claude-code",
    "model": "claude-haiku-4-5-20251001",
    "timeout_seconds": 60
  }
}
```

This shells out to `claude -p` with `--safe-mode --tools ""` (so it
can't trigger claude-log's own hooks or take any action) and
`MAX_THINKING_TOKENS=0` (thinking disabled — has no effect on Fable
models, which log a warning if configured here). **This has a real,
recurring usage cost** against your subscription (Pro/Max) or Console
usage limits, once per summarized turn — it's why this isn't the
default.

## First-Run Troubleshooting

- **Every entry says `summary_failed: true`.** Expected with no
  `summarization_endpoint` configured (`null` is the default) — this
  isn't a bug, it's the honest-failure design (see above). Configure one
  of the two shapes above to get real summaries.
- **No `.claude-log/` directory ever appears in a project.** Check the
  Prerequisite above — on Windows especially, confirm `python3` (not
  just `python`) resolves on `PATH`. Also check
  `~/.claude-log/internal.log` for hook errors (set `log_level: "debug"`
  for more detail).
- **`claude plugin install` succeeds but nothing gets logged.** Run
  `claude plugin list` and confirm `claude-log@claude-log` shows
  `Status: ✔ enabled`.

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

**Uninstalling doesn't delete `~/.claude-log/`.** Unlike a plugin's
`${CLAUDE_PLUGIN_DATA}` directory (which Claude Code cleans up
automatically on uninstall), claude-log deliberately keeps its config
and internal log at a fixed, machine-level location independent of the
plugin's own lifecycle — so your settings survive an uninstall/reinstall.
Delete `~/.claude-log/` yourself if you want a clean slate.

## Status

Core Logging is implemented and has passed a full real-world end-to-end
test (headless sessions, `--resume`, `/clear`, `/compact`,
`/claude-log-load`, an interrupted turn, and git-snapshot file tracking
across multi-commit turns and untracked directories), plus a real
marketplace install/uninstall cycle. See `CHANGELOG.md` for release
history and `BACKLOG.md` for known limitations and deferred work.

## License

MIT — see [`LICENSE`](LICENSE).
