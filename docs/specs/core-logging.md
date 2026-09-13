# Component: Core Logging

## Purpose
Manage the session logging lifecycle: track a turn across separate hook
processes, snapshot git state, call the summarization endpoint, persist
one entry per turn, and handle session boundaries (resume, clear, end)
safely.

## Responsibilities
- Accumulate one turn's prompt + assistant messages in a per-turn buffer
  (hooks share no memory — see `docs/adr/0006-*`)
- Snapshot git state at turn start and turn end; diff to find touched
  files (see `docs/adr/0004-*`)
- Call the summarization endpoint with recent log context + this turn's
  text; append one entry per turn (or a marker entry on failure)
- Detect and mark orphaned turns (crash, interrupt, or an unconfirmed
  overlap scenario) rather than merge or fabricate content
- Handle `/clear` context-reset boundaries and manual re-ingestion via
  `/claude-log-load`

## Data Model

### File Locations
```
~/.claude-log/config.json            # plugin config (machine-scoped)
~/.claude-log/internal.log           # claude-log's own operational log
<project>/.claude-log/
  logs/<session_id>.jsonl            # one file per session, append-only
  .buffers/<session_id>__<prompt_id>.json   # one file per in-flight turn
  .state/<session_id>.json           # context-reset + re-ingestion state
```
See `docs/adr/0002-*` for why plugin config/internal log are home-level
while session data stays project-level, and `docs/adr/0006-*` for the
buffer naming.

### Log Entry
See `SPEC.md` for the full schema. One shape only: `turn_id, timestamp,
summary, refs{commit_before, commit_after, files}` — or a
`summary_failed`/`turn_lost` marker in place of `summary` on failure.

### Turn Buffer
```json
{ "prompt": "string or null", "assistant_messages": ["string", ...],
  "commit_before": "hash or null",
  "dirty_before": {"path": "content hash", "...": "..."} }
```
Written atomically (temp file + `os.replace`) on every mutation, same
pattern as the scrapped branch's buffer — that part worked correctly.

### Session State (`.state/<session_id>.json`)
```json
{ "reset_at_entry_index": 12, "reingested_count": null }
```
`null`/absent fields mean "no reset has happened" — see
`docs/adr/0007-*` for the window-size formula this feeds.

## Interface

### Public Methods

#### `initialize_or_resume(project_root: str, session_id: str, config: dict) -> str`
Return the log path, creating the file only if it doesn't already exist.
Never truncates an existing log.

#### `get_recent_entries(log_path: str, session_id: str, project_root: str, configured_window: int) -> list[dict]`
Returns the last `min(configured_window, reingested_count_or_0 +
entries_since_reset)` entries — see `docs/adr/0007-*`. With no reset
state on disk (plain `startup`, or a **resumed** session — `SessionStart`
never writes a reset marker for `source: "resume"`), this collapses to a
plain "last N entries" read: a resumed session's summarization
immediately has full recent-log context, no `/claude-log-load` needed.
The reset marker only ever exists after a `/clear`.

#### `append_entry(log_path: str, entry: dict) -> None`
Single `write()` append (sufficient under the single-writer assumption —
see Known Limitations).

#### `snapshot_git_state(project_root: str, dirty_paths: list[str] | None = None) -> dict`
Returns `{"commit": str | None, "dirty": {path: hash}}`. Called once at
`UserPromptSubmit` (no `dirty_paths` yet — reads `git status --porcelain`
itself) and once at `Stop` (re-hashes the same paths plus any new ones).

#### `files_touched(commit_before, commit_after, dirty_before, dirty_after, project_root) -> list[str]`
Union of `git diff --name-only commit_before..commit_after` and every
path whose `dirty_after` hash differs from (or is absent from)
`dirty_before` — see `docs/adr/0004-*`.

#### `sweep_orphaned_buffers(project_root: str, session_id: str, current_prompt_id: str) -> list[dict]`
Lists `.buffers/` for `<session_id>__*` files other than the current
turn's; returns a `turn_lost` marker entry per leftover file found, and
deletes them. Called from `UserPromptSubmit` and `SessionEnd` (see
`docs/adr/0006-*` and `docs/adr/0007-*`).

## Configuration (`~/.claude-log/config.json`)
```json
{
  "enabled": true,
  "recent_context_window": 10,
  "summarization_endpoint": {
    "url": "http://localhost:8181/v1/chat/completions",
    "model": "mlx-community/Qwen3.5-4B-4bit",
    "api_key": null,
    "extra_params": {"temperature": 0.5, "top_p": 0.5, "seed": 42,
                      "max_tokens": 512}
  },
  "log_level": "info"
}
```
`log_level` controls `~/.claude-log/internal.log` verbosity
(`debug`/`info`/`warning`/`error`, via stdlib `logging` +
`RotatingFileHandler`).

## Integration Points

### Hooks
`UserPromptSubmit`, `MessageDisplay`, `Stop`, `SessionStart`,
`SessionEnd` — see `SPEC.md`'s Integration Points for what each does.
Shipped via a personal skills-directory plugin (`docs/adr/0001-*`), so
registration lives in the plugin's `hooks/hooks.json`, not any single
project's `.claude/settings.json`.

Confirmed input fields, from the hooks reference's per-event sections
(not just its summary table — see PLAN.md's note on the one remaining
ambiguity):
- **`UserPromptSubmit`**: `session_id, cwd, prompt_id, prompt, ...`
  (corrected: an earlier summary-table pass wrongly said `user_prompt`)
- **`MessageDisplay`**: `session_id, cwd, prompt_id, turn_id, message_id,
  index, final, delta` — `prompt_id` is a universal common field (present
  on every event once the first prompt has been submitted), so it's
  expected alongside `MessageDisplay`'s own `turn_id`/`message_id`, even
  though the doc's own example payload happens not to show it. Fires once
  per batch of newly-completed lines (interactive) or once with the full
  message (`index: 0, final: true`) in non-interactive/SDK runs. `delta`
  is incremental text, not the full message, in the interactive case —
  the buffer must accumulate `delta` across calls for the same
  `message_id`, using `final` to know when a message is complete.
- **`Stop`**: `session_id, cwd, prompt_id, last_assistant_message, ...`.
  **Does not fire on a Ctrl+C interrupt** (confirmed directly from the
  hooks reference's own Stop section) — this is exactly why the
  `turn_lost` orphan-sweep mechanism (docs/adr/0006) exists, not a
  hypothetical edge case
- **`SessionStart`**: `session_id, cwd, source, ...` — `source` is
  `startup|resume|clear|compact|fork`, present directly in the input
  (not only inferred from which matcher fired), confirmed from the
  hooks reference's own SessionStart section (see ADR-0007)
- **`SessionEnd`**: `session_id, cwd, reason` — `reason` is one of
  `clear|resume|logout|prompt_input_exit|other`; fires on `/clear` and
  `/resume` too, not only true session termination.

### Summarization Endpoint
OpenAI-compatible `/v1/chat/completions`. Reference request shape (not
committed as runnable code — `curl.sh` at the repo root is a local,
gitignored reference file the user keeps for their own MLX server):
```json
{
  "model": "mlx-community/Qwen3.5-4B-4bit",
  "messages": [
    {"role": "system", "content": "You are claude-log's turn summarizer. ..."},
    {"role": "user", "content": "Recent turns:\n...\n\nCurrent turn:\n..."}
  ],
  "stream": false,
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "summary_response",
      "schema": {
        "type": "object",
        "properties": {"summary": {"type": "string"}},
        "required": ["summary"],
        "additionalProperties": false
      },
      "strict": true
    }
  }
}
```
Full turn text (prompt + all assistant messages) is passed uncut; the
endpoint's own model does the condensing, not claude-log — pre-truncating
before the summarization step just reintroduces the same flow-breaking
bug one step earlier (see `docs/adr/0005-*`). Sampling parameters
(`temperature`, `top_p`, `seed`, `max_tokens`) and any model-specific
extras (e.g. Qwen's `chat_template_kwargs`) are passed through from
config verbatim rather than hardcoded, since they're model-dependent.

### `/claude-log-load` skill
A plugin-shipped skill, not a hook (hooks can't be triggered by typed
input). Takes an optional count argument (default 10), reads that many
recent entries from the current session's log, and records the count in
`.state/<session_id>.json`.

## Error Handling
- **Summarization endpoint unreachable/timeout/malformed response**:
  append a `summary_failed: true` marker entry (no fabricated text);
  surface via `systemMessage` on the `Stop` hook's output
- **Orphaned turn buffer found** (crash, interrupt, or an unconfirmed
  overlap scenario): append a `turn_lost: true` marker entry, delete the
  stale buffer file
- **Disk write failure**: log to `~/.claude-log/internal.log` at `error`
  level; never block the user's session (hooks always exit 0 — see
  guarded `run()`/`main()` split, carried over from the scrapped branch)
- **Not a git repository**: `commit_before`/`commit_after` are `null`,
  `files` is derived from the dirty-hash diff alone

## Testing Strategy
- Unit tests: buffer atomicity, JSONL append/tail-read, git-snapshot
  diffing (including the pre-existing-dirty-file exclusion case from
  `docs/adr/0004-*`), window-size formula, orphan sweep
- Integration tests: full hook-to-hook turn sequences via canned stdin
  fixtures, including an interrupted-turn scenario (leftover buffer →
  `turn_lost` on the next turn)
- Manual smoke test: a real Claude Code session exercising resume,
  `/clear`, `/claude-log-load`, and a normal turn — see `PLAN.md`'s
  Verification section

## Known Limitations
See `BACKLOG.md` for the current, authoritative list (file locking, log
rotation, amended-commit dangling refs, tail-read performance at scale,
and the open research item on interrupt/queueing behavior).

## Future Enhancements
See `BACKLOG.md`'s `feature`/`good-to-have` sections (real local model
setup guidance, benchmarking suite, viewing/export tooling).
