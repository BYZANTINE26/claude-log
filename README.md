<div align="center">

# 🪶 claude-log

**Your Claude Code sessions, remembered — without the token bill.**

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Claude Code Plugin](https://img.shields.io/badge/claude%20code-plugin-5A32FB.svg)](.claude-plugin/plugin.json)

An append-only, token-efficient session logger for Claude Code. One honest
summary per turn, not your whole conversation history replayed back at you.

[Why](#-why-this-exists) •
[How it works](#-how-it-works) •
[Install](#-installation) •
[Configure](#%EF%B8%8F-configuration) •
[Troubleshooting](#-first-run-troubleshooting)

</div>

---

## 🤔 Why This Exists

> [!NOTE]
> Claude Code sessions accumulate context fast. Re-sending full
> conversation history (or a bloated "rich" summary that re-embeds raw
> content) to reconstruct where you were burns tokens — worse the longer
> a project runs.

- 💸 **Long sessions get expensive.** Full-history replay or verbose
  re-summarization costs tokens on every single turn.
- 🧵 **Existing tools lose the journey.** Aggressive compression erases
  *how* you got to the current state, not just what it is.
- 🎭 **Silent failure is worse than no summary.** A tool that fabricates a
  placeholder summary when it can't actually summarize is lying to you at
  the exact moment you need to trust the log most.
- 🧹 **`/clear` should mean clear.** A fresh context window shouldn't
  quietly get fed the last N log entries from before the clear — that's a
  context leak, not a fresh start.
- 🔌 **Setup friction kills adoption.** A tool that needs per-project hook
  configuration doesn't get installed; one that works everywhere the
  moment you install it does.

## ⚙️ How It Works

1. **Install once, as a personal plugin** — hooks register for every
   project on the machine, no per-project setup (see [Installation](#-installation)).
2. Each turn's assistant messages are captured incrementally via
   `MessageDisplay` and buffered to disk, keyed by
   `<session_id>__<prompt_id>` so a crash or interrupt never corrupts
   another turn's buffer.
3. On `Stop`, the buffered turn (prompt + assistant messages) plus a
   git-snapshot diff of files touched during the turn are sent to a
   summarization endpoint — either your own OpenAI-compatible server, or
   your existing Claude Code login (see [Configuration](#%EF%B8%8F-configuration)).
4. The summary is appended as one JSON line to
   `<project>/.claude-log/logs/<session_id>.jsonl`.

   > [!IMPORTANT]
   > If summarization fails for any reason, an honest `summary_failed`
   > marker is written instead — **never** a fabricated or rule-based
   > placeholder summary.

5. `/clear` gates how much of the log feeds back into future
   summarization calls (growing back up to the configured window as new
   turns land); `/claude-log-load [count]` lets you manually re-ingest
   recent entries after a clear. Resuming a session (`--resume` / picking
   up a prior session) is **not** gated — it gets the full configured
   window immediately.
6. Interrupted or crashed turns (no `Stop` fires on a `Ctrl+C` interrupt)
   are swept into `turn_lost` markers on the next `UserPromptSubmit` or
   on `SessionEnd`, so nothing silently vanishes from the log.

Like an event-sourced log or a RAFT log, claude-log stores the steps, not
a replicated snapshot of state at every step — state is reconstructed
cheaply from a handful of recent entries, without redundancy.

📖 See [`SPEC.md`](SPEC.md) and
[`docs/specs/core-logging.md`](docs/specs/core-logging.md) for the full
design, and [`docs/adr/`](docs/adr/) for the reasoning behind each of
these decisions.

## 🖥️ What This Does to Your Machine

Once installed, claude-log runs automatically for **every project** you
open Claude Code in — there's no per-project opt-in.

> [!TIP]
> Nothing leaves your machine unless you configure a summarization
> endpoint yourself. No endpoint configured → every turn just logs a
> `summary_failed` marker, locally.

Concretely, it:

| Action | Detail |
|---|---|
| ✍️ **Writes** | One JSON line per turn to `<project>/.claude-log/logs/<session_id>.jsonl`, plus transient files under `.claude-log/.buffers/` and `.state/` (cleaned up during normal operation). |
| 🔍 **Reads git state** | `git status`, `git diff --name-only`, `git hash-object` — to figure out which files a turn touched. Never runs `git commit`, `git push`, or anything that changes your repo. |
| 📡 **Sends data (opt-in only)** | Only if you configure a `summarization_endpoint`: the turn's prompt and assistant messages, to either your own server or a `claude -p` subprocess using your existing login. |
| 🗂️ **Keeps its own state** | Settings and operational log live at `~/.claude-log/` (see [Where Things Live](#-where-things-live)), separate from any project. |

It never reads or sends your actual file contents anywhere except your
own configured summarization endpoint (or your own Claude Code login),
and never modifies files in your project.

## 📦 Installation

> [!IMPORTANT]
> Every hook is a Python script, invoked as `python3 <script path>`
> (exec form, for portability — see [`hooks/hooks.json`](hooks/hooks.json)).
> **`python3` (3.10+) must be on `PATH`.**
>
> On macOS and Linux this is almost always already true. On Windows, a
> standard python.org install only adds `python.exe`/`py.exe` to `PATH`,
> not `python3.exe` — add a `python3` alias/shim yourself, or install
> Python through a distribution that provides one (e.g. the Microsoft
> Store package, or WSL). **This hasn't been tested on a real Windows
> machine** — if hooks silently fail to run there, this is the first
> thing to check.

<details open>
<summary><strong>Install through Claude Code (recommended)</strong></summary>

claude-log ships as a real Claude Code plugin, distributed through its
own marketplace file
([`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json))
in this repo:

```sh
claude plugin marketplace add BYZANTINE26/claude-log
claude plugin install claude-log@claude-log
```

That's it — no per-project setup, hooks apply to every project on the
machine from then on.

</details>

<details>
<summary><strong>Alternative: load without installing</strong></summary>

For trying it out or developing on it, load it directly for a single
session, without registering a marketplace:

```sh
claude --plugin-dir /path/to/claude-log
```

</details>

## ⚙️ Configuration

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
| `summarization_endpoint` | `null` | See below. `null` means every turn logs an honest `summary_failed` marker — there is no rule-based fallback, by design (see [`docs/adr/0003`](docs/adr/)). |
| `log_level` | `"info"` | `debug`/`info`/`warning`/`error` for `~/.claude-log/internal.log`. |

`summarization_endpoint` has two independent shapes — pick one.

<details>
<summary><strong>🌐 Your own OpenAI-compatible server</strong></summary>

Local model, or any provider speaking the `/v1/chat/completions`
contract:

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

</details>

<details>
<summary><strong>🔑 Through your existing Claude Code login</strong></summary>

No separate server, API key, or account:

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
models, which log a warning if configured here).

> [!WARNING]
> This has a real, recurring usage cost against your subscription
> (Pro/Max) or Console usage limits, once per summarized turn — it's why
> this isn't the default.

</details>

## 🩺 First-Run Troubleshooting

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

## 🗂️ Where Things Live

| Path | What |
|---|---|
| `~/.claude-log/config.json` | User settings (this machine, all projects). |
| `~/.claude-log/internal.log` | claude-log's own rotating operational log, level controlled by `log_level`. |
| `<project>/.claude-log/logs/<session_id>.jsonl` | The actual session logs, one file per session, per project. |
| `<project>/.claude-log/.buffers/`, `.state/` | Transient, disposable working files. Safe to delete; claude-log recreates them as needed. |

> [!TIP]
> Since `<project>/.claude-log/` lives inside the project directory, add
> it to that project's `.gitignore` unless you intend to version your
> session logs — otherwise claude-log's own writes (e.g. its `.state/`
> file) will show up as "files touched" on whatever turn happens to
> trigger them, since they're genuinely part of the working tree's diff
> at that point.

> [!NOTE]
> **Uninstalling doesn't delete `~/.claude-log/`.** Unlike a plugin's
> `${CLAUDE_PLUGIN_DATA}` directory (which Claude Code cleans up
> automatically on uninstall), claude-log deliberately keeps its config
> and internal log at a fixed, machine-level location independent of the
> plugin's own lifecycle — so your settings survive an uninstall/reinstall.
> Delete `~/.claude-log/` yourself if you want a clean slate.

## 🧭 Design Principles

These aren't implementation details — they're the constraints that shape
every decision above:

- **Append-only, write-once.** Logs are a chronological record, never
  rewritten in place.
- **One entry shape.** A summary plus metadata — no separate "rich mode"
  that re-embeds raw prompt/tool content and defeats the whole point.
- **Honesty over completeness.** A missing or failed summary is always an
  explicit marker (`summary_failed`, `turn_lost`), never silently dropped
  or replaced with a plausible-sounding placeholder.
- **Local-first.** No cloud API calls unless you explicitly configure one
  — either your own endpoint or your own existing login.
- **Zero per-project setup.** Install once; every project on the machine
  is covered from then on.

## ✅ Status

Core Logging is implemented and has passed a full real-world end-to-end
test (headless sessions, `--resume`, `/clear`, `/compact`,
`/claude-log-load`, an interrupted turn, and git-snapshot file tracking
across multi-commit turns and untracked directories), plus a real
marketplace install/uninstall cycle.

See [`CHANGELOG.md`](CHANGELOG.md) for release history and
[`BACKLOG.md`](BACKLOG.md) for known limitations and deferred work.

## 🤝 Contributing

Issues and PRs welcome at
[github.com/BYZANTINE26/claude-log](https://github.com/BYZANTINE26/claude-log).

> [!IMPORTANT]
> Read [`SPEC.md`](SPEC.md) and
> [`docs/specs/core-logging.md`](docs/specs/core-logging.md) before
> touching core logging behavior — several decisions (honest-failure,
> single entry shape, `/clear` gating) are deliberate and documented as
> ADRs, not oversights.

## 📄 License

MIT — see [`LICENSE`](LICENSE).
</content>
