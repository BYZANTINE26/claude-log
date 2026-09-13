# Plan: claude-log Core Logging (redo)

## Context
The first implementation attempt (`feature/core-logging-mvp`) was
reviewed and scrapped — real design gaps (tool-payload leakage, no real
turn identity, no crash/interrupt safety, ambiguous file-touch tracking,
per-project-only distribution) surfaced after the branch fired its own
hooks live. This plan replaces it entirely, incorporating everything
settled during the `grill-with-docs` redo: `INTENT.md`, `SPEC.md`,
`docs/specs/core-logging.md`, and seven ADRs in `docs/adr/`.

This plan covers Core Logging only. Real local model *setup guidance*
(the summarizer's HTTP contract is real and final — only "which model to
run" is deferred), and benchmarking against claude-mem, remain their own
phases in `BACKLOG.md`.

## Locked-in decisions
See `docs/adr/0001` through `0007` for full reasoning. Summary:
- **Distribution**: personal skills-directory plugin (`~/.claude/skills/
  claude-log/`), not per-project hook registration (ADR-0001).
- **Storage split**: `~/.claude-log/` for plugin config + internal log;
  `<project>/.claude-log/` for session logs, buffers, and state
  (ADR-0002).
- **Log integrity**: failures and orphaned turns become explicit
  `summary_failed`/`turn_lost` marker entries, never fabricated or
  silently dropped (ADR-0003).
- **No Rich mode, no `PostToolUse`**: one entry shape; turn context is
  prompt + all assistant messages + a git-diff-derived file list, not
  per-tool-call tracking (ADR-0004, ADR-0005).
- **Turn buffers keyed by `<session_id>__<prompt_id>.json`**, so an
  interrupted or overlapping turn can never corrupt another (ADR-0006).
- **`turn_id` = Claude Code's own `prompt_id`** (a UUID), not a
  synthesized counter.
- **Session lifecycle**: `SessionStart` marks a context-reset boundary on
  `/clear`; the recent-context window naturally grows via
  `min(N, reingested_count + entries_since_reset)`; `/claude-log-load
  [count]` (default 10) is a plugin skill, not a hook; `SessionEnd` does
  a final orphan sweep (ADR-0007).
- **Summarizer**: OpenAI-compatible `/v1/chat/completions` endpoint,
  configured (URL, model, auth, sampling params) in
  `~/.claude-log/config.json`. Full turn text passed uncut — no
  pre-truncation.
- **Internal logging**: stdlib `logging` + `RotatingFileHandler` to
  `~/.claude-log/internal.log`, levels `debug/info/warning/error`
  controlled by config, no stderr.

## File/module layout
```
.claude-plugin/
  plugin.json                # name, description, version
hooks/
  hooks.json                 # registers all 5 hooks directly against
                              # claude_log/hooks/*.py — no wrapper scripts,
                              # plugins resolve their own root, so the
                              # sys.path-shim-per-file that per-project
                              # hook registration needed doesn't apply
skills/
  claude-log-load/
    SKILL.md                 # /claude-log-load [count]
claude_log/
  __init__.py
  config.py          # load ~/.claude-log/config.json, DEFAULT_CONFIG,
                      # home/project path resolution, rotating internal
                      # logger setup — one "plugin environment" module
  buffer.py           # atomic per-turn buffer (prompt, assistant_messages,
                       # commit_before, dirty_before), orphan sweep
  logger.py            # initialize_or_resume, append_entry, build_entry,
                       # get_recent_entries + its window-size formula
                       # (reads/writes .state/<session_id>.json itself —
                       # the only caller of that state, so it lives here)
  summarizer.py        # summarize(), call_openai_compatible_endpoint()
  git_snapshot.py       # snapshot_git_state(), files_touched()
  hooks/
    __init__.py
    _hook_io.py
    session_start.py
    user_prompt_submit.py
    message_display.py
    stop.py
    session_end.py
tests/
  conftest.py
  test_buffer.py
  test_logger.py
  test_summarizer.py
  test_git_snapshot.py
  test_hooks_*.py (one per hook)
  fixtures/
pyproject.toml
```
Dropped from the original sketch: a `bin/` directory of thin wrapper
scripts and separate `paths.py`/`session_state.py`/`internal_log.py`
modules — each was either boilerplate for a problem the plugin
architecture already solves (`bin/`), or a handful of one-line functions
with a single caller that didn't earn a separate file (ponytail:
"fewest files possible... once you understand the problem").

## Module interfaces (signatures only)

**config.py**
```python
DEFAULT_CONFIG = {
    "enabled": True,
    "recent_context_window": 10,
    "summarization_endpoint": None,  # dict: url/model/api_key/extra_params
    "log_level": "info",
}
def load_config() -> dict: ...  # reads ~/.claude-log/config.json

def plugin_home() -> str: ...                  # ~/.claude-log
def project_log_dir(project_root: str) -> str: ...  # <project>/.claude-log
def log_file_path(project_root: str, session_id: str) -> str: ...
def buffer_path(project_root: str, session_id: str, prompt_id: str) -> str: ...
def state_path(project_root: str, session_id: str) -> str: ...

def get_logger() -> logging.Logger: ...  # rotating handler, level from config
```

**buffer.py**
```python
def start_turn(buffer_path: str, prompt_text: str,
               commit_before: str | None, dirty_before: dict) -> None: ...
def append_assistant_message(buffer_path: str, message_text: str) -> None: ...
def read_and_clear(buffer_path: str) -> dict: ...
def sweep_orphaned(project_root: str, session_id: str,
                    keep_prompt_id: str) -> list[dict]: ...  # -> turn_lost markers
```

**logger.py**
```python
def initialize_or_resume(project_root: str, session_id: str) -> str: ...
def get_recent_entries(project_root: str, session_id: str,
                        configured_window: int) -> list[dict]: ...
    # internally: reads/writes .state/<session_id>.json (mark_context_reset,
    # record_reingestion happen via this module too) and applies
    # min(configured_window, reingested_count + entries_since_reset)
def append_entry(log_path: str, entry: dict) -> None: ...
def build_entry(turn_id: str, timestamp: str, summary: str | None,
                 refs: dict, failure_flag: str | None = None) -> dict: ...
def mark_context_reset(project_root: str, session_id: str) -> None: ...
def record_reingestion(project_root: str, session_id: str, count: int) -> None: ...
```

**summarizer.py**
```python
def summarize(recent_entries: list[dict], prompt: str,
              assistant_messages: list[str], config: dict) -> str | None: ...
    # None on failure -> caller writes a summary_failed marker
def call_openai_compatible_endpoint(endpoint_config: dict,
                                     recent_entries: list[dict],
                                     prompt: str,
                                     assistant_messages: list[str]) -> str: ...
```

**git_snapshot.py**
```python
def snapshot_git_state(project_root: str,
                        known_dirty_paths: set[str] | None = None) -> dict: ...
    # {"commit": str | None, "dirty": {path: content_hash}}
def files_touched(commit_before, commit_after, dirty_before, dirty_after,
                   project_root: str) -> list[str]: ...
```

## Plugin manifest sketch
```json
// .claude-plugin/plugin.json
{"name": "claude-log", "description": "Append-only, token-efficient session logging.", "version": "0.1.0"}
```
```json
// hooks/hooks.json
{
  "hooks": {
    "SessionStart": [{"matcher": "*", "hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/claude_log/hooks/session_start.py"}]}],
    "UserPromptSubmit": [{"matcher": "*", "hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/claude_log/hooks/user_prompt_submit.py"}]}],
    "MessageDisplay": [{"hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/claude_log/hooks/message_display.py"}]}],
    "Stop": [{"matcher": "*", "hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/claude_log/hooks/stop.py"}]}],
    "SessionEnd": [{"matcher": "*", "hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/claude_log/hooks/session_end.py"}]}]
  }
}
```
Each hook script is directly executable (`#!/usr/bin/env python3` +
`chmod +x`) and resolves its own package root once, at the top, before
importing `claude_log` — the one-line equivalent of what the dropped
`bin/` wrappers did, without a second file per hook.

## Order of implementation
0. **One remaining field-name ambiguity**: `MessageDisplay`'s documented
   example payload doesn't show `prompt_id` even though it's supposedly a
   common field (v2.1.196+) — only its own `turn_id`/`message_id`. The
   hook code reads `hook_input.get("prompt_id") or hook_input.get("turn_id")`
   defensively rather than guessing which is present; confirmed for real
   during the manual smoke test (step 8), not blocking implementation.
   All other fields for all five hooks are confirmed directly from the
   hooks reference's per-event sections (not just the summary table).
1. `config.py` — settings load, path resolution, internal logger setup;
   pure/independent, unit tested immediately.
2. `git_snapshot.py` — the riskiest new piece (hash-diff correctness for
   pre-existing dirty/untracked files per ADR-0004); tested thoroughly
   in isolation before anything depends on it.
3. `buffer.py` — atomic per-turn state + orphan sweep.
4. `logger.py` — JSONL append/tail-read, including the window-size
   formula and `.state/<session_id>.json` reset/re-ingestion handling
   (ADR-0007), tested against those scenarios directly.
5. `summarizer.py` — OpenAI-compatible HTTP call, tested against a local
   `http.server` fixture for success, timeout, and malformed-response
   paths (all three must yield `summary_failed`, never fabricated text).
6. `hooks/_hook_io.py`, then the five hook modules (each directly
   executable, no wrapper scripts) + the `claude-log-load` skill.
7. Assemble the plugin structure (`.claude-plugin/plugin.json`,
   `hooks/hooks.json`), test locally via `claude --plugin-dir`.
8. Manual smoke test (see Verification) in a real Claude Code session.
9. Update `BACKLOG.md`, `CHANGELOG.md`, `README.md`.

## Verification
**Unit tests** (`pytest`, no live Claude Code needed): buffer atomicity
and orphan sweep; git-snapshot diffing including the pre-existing-dirty-
file exclusion case; window-size formula across reset/no-reset/
re-ingestion states; summarizer success/timeout/malformed-response paths
all yielding the correct marker on failure; hook sequences via canned
fixtures including an interrupted-turn scenario.

**Manual smoke test** (real Claude Code session, `claude --plugin-dir`):
1. Fresh session: confirm `<project>/.claude-log/logs/<session_id>.jsonl`
   appears after the first completed turn, not at `SessionStart`.
2. One small edit turn: confirm one log line, plausible summary,
   `refs.commit_before`/`commit_after`, and `refs.files` containing the
   edited path.
3. `/clear`, then one turn with no `/claude-log-load`: confirm the
   summarizer receives empty/near-empty recent context.
4. `/claude-log-load 5`, then a turn: confirm the window formula reflects
   5 + entries-since-reset.
5. Interrupt a turn (Ctrl+C) mid-generation, then submit a new prompt:
   confirm a `turn_lost` marker appears and the new turn logs cleanly.
6. Resume the same session: confirm the `.jsonl` file grows, not
   recreated.

## Backlog items
See `BACKLOG.md` — kept as the single source of truth, not duplicated
here.
