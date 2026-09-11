# Plan: claude-log Core Logging MVP

## Context
claude-log needs its first real implementation: an append-only, per-session,
per-project JSONL log where each completed turn gets a 1-2 line summary
generated from only recent log context (not full history), avoiding the
token waste of tools like claude-mem. This was settled via brainstorming
(INTENT.md), specified in SPEC.md and docs/specs/core-logging.md, and refined
through this planning session: Python, a stub (rule-based) summarizer behind
the real pluggable HTTP contract, and hooks that batch a whole turn
(UserPromptSubmit + PostToolUse + Stop) into one log entry via a per-turn
buffer, since each hook fires as a separate process with no shared memory.

This plan covers the MVP only: core logging + stub summarization. Real local
model integration and benchmarking against claude-mem are separate,
subsequent phases (see Deferred/Backlog below).

## Locked-in decisions
- **Language**: Python, stdlib only (`urllib`, `json`, `subprocess`, `os`).
- **Summarizer**: `summarize()` tries `config["summarization_endpoint"]` via
  HTTP (5s timeout) if set; otherwise/on-failure falls back to an in-process
  rule-based heuristic. MVP config leaves the endpoint unset, so it always
  uses the rule-based path — but the HTTP code path is real and tested, so
  swapping in a real local model later is a config change only.
- **Hooks**: `SessionStart`, `UserPromptSubmit`, `PostToolUse`, `Stop`.
  Turn data accumulates in a per-turn buffer file across the first three;
  `Stop` reads+clears the buffer, summarizes once, and appends one log entry.
- **Buffer location**: `.claude/logs/.buffers/session_<id>.json` (kept out of
  the `.jsonl` glob, name says exactly what it is).
- **turn_id**: synthesized as `f"{session_id}:{entry_index}"` (sequential
  counter per session) since Claude Code may not expose a distinct per-turn
  ID — `entry_index` is just the current line count of the session's log.
- **Hook invocation**: absolute script paths (not `python3 -m`), to avoid
  depending on `cwd`/`PYTHONPATH` assumptions Claude Code's hook runner may
  or may not satisfy. Each script inserts the repo root onto `sys.path`
  itself before importing `claude_log`.
- **Crash-mid-turn buffer leak** (Stop never fires, stale buffer bleeds into
  next turn): accepted as an MVP limitation, not fixed now — see Backlog.

## File/module layout
```
claude_log/
  __init__.py
  config.py          # load "logging" key from .claude/settings.json
  paths.py           # project_root, log path, buffer path resolution
  buffer.py          # atomic reset/append_prompt/append_tool_call/read_and_clear
  logger.py          # initialize_or_resume, append_entry, get_recent_entries, build_entry
  summarizer.py      # summarize(), call_http_endpoint(), rule_based_summary()
  metadata.py        # current_commit_hash(), files_touched()
  hooks/
    __init__.py
    _hook_io.py      # read_hook_input(), emit_ok(), resolve_project_root()
    session_start.py
    user_prompt_submit.py
    post_tool_use.py
    stop.py
bin/
  claude_log_session_start.py   # thin absolute-path wrappers Claude Code calls
  claude_log_user_prompt_submit.py
  claude_log_post_tool_use.py
  claude_log_stop.py
tests/
  conftest.py
  test_buffer.py
  test_logger.py
  test_summarizer.py
  test_hooks_session_start.py
  test_hooks_user_prompt_submit.py
  test_hooks_post_tool_use.py
  test_hooks_stop.py
  fixtures/
    session_start_new.json
    session_start_resume.json
    user_prompt_submit.json
    post_tool_use_edit.json
    post_tool_use_bash.json
    stop.json
pyproject.toml
```
Every module stays well under the 600-line cap given this scope; `hooks/*.py`
are thin (parse stdin → call into `claude_log` → emit stdout/exit 0).

## Module interfaces (signatures, not full code)

**config.py**
```python
DEFAULT_CONFIG = {
    "enabled": True,
    "verbosity": "slim",
    "recent_context_window": 10,
    "summarization_endpoint": None,
    "log_directory": ".claude/logs",
}
def load_config(project_root: str) -> dict: ...
```

**paths.py**
```python
def log_file_path(project_root: str, session_id: str, config: dict) -> str: ...
def turn_buffer_path(project_root: str, session_id: str) -> str: ...
```

**buffer.py** (write-tmp + `os.replace` for atomic read-modify-write)
```python
def reset_buffer(buffer_path: str) -> None: ...
def append_prompt(buffer_path: str, prompt_text: str) -> None: ...
def append_tool_call(buffer_path: str, tool_name: str,
                      result_summary: str, tool_input: dict) -> None: ...
def read_and_clear(buffer_path: str) -> dict: ...
```

**logger.py**
```python
def initialize_or_resume(project_root: str, session_id: str,
                          config: dict) -> str: ...
def get_recent_entries(log_file_path: str, count: int) -> list[dict]: ...
def append_entry(log_file_path: str, entry: dict) -> None: ...
def build_entry(turn_id: str, summary: str, refs: dict,
                 context: dict | None, verbosity: str) -> dict: ...
```

**summarizer.py**
```python
def summarize(recent_entries: list[dict], current_turn: dict,
              config: dict) -> str: ...
def call_http_endpoint(endpoint_url: str, recent_entries: list[dict],
                        current_turn: dict,
                        timeout_seconds: float = 5.0) -> str: ...
def rule_based_summary(current_turn: dict) -> str: ...
```

**metadata.py**
```python
def current_commit_hash(project_root: str) -> str | None: ...
def files_touched(tool_calls: list[dict]) -> list[str]: ...
```

**hooks/_hook_io.py**
```python
def read_hook_input() -> dict: ...
def emit_ok(extra: dict | None = None) -> None: ...
def resolve_project_root(hook_input: dict) -> str: ...
```

**hooks/{session_start,user_prompt_submit,post_tool_use,stop}.py**
Each wraps its `main()` body in try/except → log to stderr, still `exit 0`,
so a claude-log bug never blocks the user's real Claude Code session.

## `.claude/settings.json` additions
```jsonc
{
  "logging": {
    "enabled": true,
    "verbosity": "slim",
    "recent_context_window": 10,
    "summarization_endpoint": null,
    "log_directory": ".claude/logs"
  },
  "hooks": {
    "SessionStart": [{"matcher": "*", "hooks": [
      {"type": "command",
       "command": "python3 /Volumes/GBC/projects/claude-log/bin/claude_log_session_start.py"}
    ]}],
    "UserPromptSubmit": [{"matcher": "*", "hooks": [
      {"type": "command",
       "command": "python3 /Volumes/GBC/projects/claude-log/bin/claude_log_user_prompt_submit.py"}
    ]}],
    "PostToolUse": [{"matcher": "*", "hooks": [
      {"type": "command",
       "command": "python3 /Volumes/GBC/projects/claude-log/bin/claude_log_post_tool_use.py"}
    ]}],
    "Stop": [{"matcher": "*", "hooks": [
      {"type": "command",
       "command": "python3 /Volumes/GBC/projects/claude-log/bin/claude_log_stop.py"}
    ]}]
  }
}
```

## Order of implementation
0. **Ground-truth capture**: a throwaway script (in `.claude/scratchpad/`,
   per CLAUDE.md) registered as a temporary hook that dumps raw stdin JSON
   to a file, run for one real turn in this project, to confirm actual
   field names (`session_id`, `prompt`, `tool_name`, `tool_input`,
   `tool_response`, `cwd`, etc.) before writing fixtures against guesses.
1. `config.py` + `paths.py` — pure functions, unit-testable immediately.
2. `buffer.py` — atomic read/append/clear; the riskiest home-grown piece,
   tested thoroughly before anything depends on it.
3. `logger.py` — JSONL append + tail-read, independent of hooks.
4. `summarizer.py` — rule-based path first, then HTTP path tested against a
   local `http.server` fixture for both success and timeout/fallback.
5. `metadata.py` — commit hash (testable in this repo) + files-touched
   extraction from canned tool-call dicts.
6. `hooks/_hook_io.py`, then the four hook modules and their `bin/` wrappers,
   tested by feeding the real captured fixtures (from step 0) on stdin.
7. Register hooks in `.claude/settings.json`.
8. Manual smoke test in a real Claude Code session (see Verification).
9. Create/update `BACKLOG.md` with the parked items below.

## Verification
**Unit tests** (`pytest`, no live Claude Code needed):
- `test_buffer.py`: reset/append/read_and_clear round-trip simulating
  UserPromptSubmit → PostToolUse×N → Stop; assert no `.tmp` file survives.
- `test_logger.py`: valid JSONL output; correct tail slice from
  `get_recent_entries`; `initialize_or_resume` is idempotent (doesn't
  truncate an existing log on repeated calls).
- `test_summarizer.py`: rule-based summaries for edit-only, tool-only, and
  prompt-only turn shapes; HTTP path success case and timeout/fallback case
  against a local `http.server` fixture.
- `test_hooks_*.py`: feed real captured fixture JSON via monkeypatched
  stdin, run `main()` against a temp project dir, assert resulting
  buffer/log file contents. Cover: fresh session creates log+buffer; resumed
  session (existing `session_<id>.jsonl`) appends without recreating; a full
  UserPromptSubmit → PostToolUse×2 → Stop sequence yields exactly one JSONL
  line whose `refs.tools` contains both tool names.

**Manual smoke test** (real Claude Code session, this project):
1. Register hooks per the settings.json block above.
2. Start a fresh session in `/Volumes/GBC/projects/claude-log`.
3. Confirm `.claude/logs/session_<id>.jsonl` and
   `.claude/logs/.buffers/session_<id>.json` appear after `SessionStart`.
4. Make one small edit; after the turn completes, confirm exactly one JSONL
   line was appended with a plausible summary, `refs.commit` matching
   `git rev-parse HEAD`, and `refs.files` containing the edited path.
5. Resume the same session; confirm the `.jsonl` file grows, not recreated.
6. Trigger a multi-tool-call turn; confirm one log line lists all tool
   names and exactly one summarization call happened.

## Backlog items to file (per "park for later" convention)
- **technical-debt**: mid-session crash leaves stale turn-buffer data that
  merges into the next turn's summary (Stop never fired to clear it).
- **technical-debt**: no file locking; two sessions sharing a `session_id`
  would corrupt a log (single-writer assumption, unlikely but unhandled).
- **technical-debt**: no log rotation/retention policy — logs grow
  unbounded.
- **feature**: real local summarization endpoint integration (e.g. Ollama)
  to replace the rule-based stub.
- **feature**: benchmarking suite comparing claude-log vs. claude-mem on
  token usage, context fidelity, and resumability (INTENT.md success
  criterion — tracked separately as its own phase, not blocking this MVP).
- **good-to-have**: viewing/querying UI or CLI for browsing a session log.
- **good-to-have**: export log to markdown/CSV; search/filter across
  multiple session logs.
- **good-to-have**: compression/encryption for archived log files.

## Open items resolved this session (no longer open)
- Language: Python. Summarizer: stub-behind-real-contract. Hooks: all four
  listed, batched into one entry per turn. Crash handling: backlog, not MVP.
