# claude-log: Specification

## Overview
A lightweight, token-efficient session logging system for Claude Code that
maintains an append-only log of session turns with 1-2 line summaries and
metadata for seamless session resumption and deep-dive investigation.
Ships as a personal Claude Code plugin (see `docs/adr/0001-*`), so it
works on any project on the machine without per-project setup.

## Architecture

### Components
1. **Core Logging** — Hook-based session logging, log file management,
   resumability, session lifecycle (clear/resume/end handling)
2. **Summarization** — OpenAI-compatible chat-completions endpoint
   integration for turn summarization (pluggable, user-configured)
3. **Benchmarking** — Comparative analysis against existing tools (token
   usage, context fidelity, resumability); its own phase, post-MVP

### Data Flow
```
UserPromptSubmit → record prompt + git snapshot in a per-turn buffer
MessageDisplay(×N) → append each assistant message to the same buffer
Stop → read+clear buffer, snapshot git again, diff files touched,
        call summarization endpoint with recent log context + this
        turn's text, append one log entry
```

## Overall Requirements

### Functional
- **Project-scoped logging**: one log per project, one per session, at
  `<project>/.claude-log/logs/<session_id>.jsonl`
- **Resume-aware**: append to existing session log on resume, never
  recreate
- **Automatic logging**: hook-based, no manual intervention for normal
  turns
- **Manual context re-ingestion**: `/claude-log-load [count]` (default
  10) lets a user pull recent log entries into a fresh (post-`/clear`)
  context window (see `docs/adr/0007-*`)
- **Metadata preservation**: `turn_id` (Claude's own `prompt_id`),
  timestamp, commit hashes, touched files
- **Chronological narrative**: walk the log to see how a session unfolded
- **Log integrity**: failures and interruptions are recorded as explicit
  marker entries, never fabricated summaries or silent gaps (see
  `docs/adr/0003-*`)

### Non-Functional
- **Token efficiency**: <20% of claude-mem's token cost for equivalent
  context preservation
- **Durability**: append-only, no data loss or mutation
- **Portability**: session logs travel with the project; plugin
  configuration and its own operational log are machine-scoped (see
  `docs/adr/0002-*`)
- **Safety under interruption/overlap**: a crashed, interrupted, or
  overlapping turn can never corrupt another turn's data (see
  `docs/adr/0006-*`)

## Log Entry Schema
There is one entry shape — no separate "rich" mode (see `docs/adr/0004-*`
for why re-embedding raw turn content was dropped).

```json
{
  "turn_id": "prompt_id (UUID) from Claude Code",
  "timestamp": "ISO 8601 string",
  "summary": "1-2 line human-readable summary",
  "refs": {
    "commit_before": "git commit hash at turn start (or null)",
    "commit_after": "git commit hash at turn end (or null)",
    "files": ["files changed during the turn, tracked or untracked"]
  }
}
```

On failure, a marker entry replaces `summary` with a boolean flag instead
of fabricated text (see `docs/adr/0003-*`):
```json
{
  "turn_id": "...",
  "timestamp": "...",
  "summary_failed": true,
  "refs": { "...": "..." }
}
```
```json
{
  "turn_id": "...",
  "timestamp": "...",
  "turn_lost": true
}
```

## Integration Points

### Claude Code Hooks
- `UserPromptSubmit` — records the prompt and a git snapshot
  (`commit_before` + hashed dirty-file set) into the turn's buffer
- `MessageDisplay` — accumulates each message's `delta` text by
  `message_id` (delivered incrementally in interactive sessions, in full
  in non-interactive/SDK runs — see `docs/specs/core-logging.md`), and
  appends the completed message (on `final: true`) to the turn's buffer
  (see `docs/adr/0005-*`)
- `Stop` — reads+clears the buffer, snapshots git again, computes
  touched files, summarizes, appends the log entry
- `SessionStart` — on `source: "clear"`, records a context-reset marker
  (see `docs/adr/0007-*`). On `source: "resume"` (or plain `startup`),
  it does nothing: no reset marker exists, so the full configured
  `recent_context_window` of prior log entries is available to the
  summarizer immediately — a resumed session's context was never
  cleared, so there's nothing to gate
- `SessionEnd` — final orphan-buffer sweep for turns that never reached
  `Stop` (see `docs/adr/0007-*`)

### Turn identity
`turn_id` is Claude Code's own `prompt_id` (a UUID present on every hook
event for a turn) — not a synthesized counter.

### Summarization Endpoint
- OpenAI-compatible `/v1/chat/completions` contract, endpoint URL/model/
  auth configured in `~/.claude-log/config.json`; see `curl.sh` for a
  reference request/response shape
- Input: recent log summaries + the current turn's full prompt and
  assistant-message text (never truncated pre-summarization — see
  Q2 decision, folded into `docs/specs/core-logging.md`)
- Output: a structured `{"summary": "..."}` response
- On failure (unreachable, timeout, malformed response): no fabricated
  fallback text — a `summary_failed` marker entry instead

## Deferred (Post-MVP)
See `BACKLOG.md` for the full, current list (file locking, log rotation,
real local model setup guidance, benchmarking suite, viewing/export
tooling, and open research items).

## Success Criteria
1. Reduced token usage: benchmark shows <20% of claude-mem's cost
2. Context richness: new session can resume accurately from log + metadata
3. Easy resumption: seamless pick-up without re-reading full history
4. Proven superiority: comparative benchmarking vs. existing tools
5. Log integrity: no fabricated or silently-dropped turns
