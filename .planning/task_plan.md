# Task Plan: Core Logging MVP

Structured from the approved `.claude/plans/PLAN.md`. This file tracks
execution only — it does not redefine the plan; see PLAN.md for full
context, rationale, and interfaces.

## Locked-in decisions (do not re-litigate)
- Language: Python, stdlib only.
- Summarizer: stub (rule-based) behind the real pluggable HTTP contract.
- Hooks: SessionStart, UserPromptSubmit, PostToolUse, Stop — batched into
  one JSONL entry per turn via a per-turn buffer file.
- Buffer location: `.claude/logs/.buffers/session_<id>.json`.
- turn_id: synthesized `f"{session_id}:{entry_index}"`.
- Hook invocation: absolute script paths in `bin/`, not `python3 -m`.
- Crash-mid-turn buffer leak: accepted MVP limitation (see BACKLOG.md).

## Phases

### Phase 0 — Ground-truth capture
- [ ] Write throwaway stdin-dump script in `.claude/scratchpad/`
- [ ] Register it as a temporary hook, run one real turn
- [ ] Confirm actual field names (session_id, prompt, tool_name,
      tool_input, tool_response, cwd, etc.)
- [ ] Remove temporary hook registration once captured

### Phase 1 — Foundation modules
- [ ] `claude_log/config.py` — `DEFAULT_CONFIG`, `load_config()`
- [ ] `claude_log/paths.py` — `log_file_path()`, `turn_buffer_path()`
- [ ] Unit tests for both (pure functions, no I/O side effects beyond
      reading settings.json)

### Phase 2 — Buffer (riskiest piece, land + test before anything depends on it)
- [ ] `claude_log/buffer.py` — `reset_buffer()`, `append_prompt()`,
      `append_tool_call()`, `read_and_clear()` (write-tmp + `os.replace`)
- [ ] `tests/test_buffer.py` — round-trip, no `.tmp` file survives

### Phase 3 — Logger
- [ ] `claude_log/logger.py` — `initialize_or_resume()`, `append_entry()`,
      `get_recent_entries()`, `build_entry()`
- [ ] `tests/test_logger.py` — valid JSONL, correct tail slice, idempotent
      initialize_or_resume

### Phase 4 — Summarizer
- [ ] `claude_log/summarizer.py` — `summarize()`, `call_http_endpoint()`,
      `rule_based_summary()`
- [ ] `tests/test_summarizer.py` — rule-based cases (edit-only, tool-only,
      prompt-only) + HTTP success/timeout-fallback against local
      `http.server` fixture

### Phase 5 — Metadata
- [ ] `claude_log/metadata.py` — `current_commit_hash()`, `files_touched()`
- [ ] Unit tests (git hash testable in this repo; files_touched from
      canned tool-call dicts)

### Phase 6 — Hooks
- [ ] `claude_log/hooks/_hook_io.py` — `read_hook_input()`, `emit_ok()`,
      `resolve_project_root()`
- [ ] `claude_log/hooks/session_start.py`
- [ ] `claude_log/hooks/user_prompt_submit.py`
- [ ] `claude_log/hooks/post_tool_use.py`
- [ ] `claude_log/hooks/stop.py`
- [ ] `bin/claude_log_*.py` thin absolute-path wrappers
- [ ] `tests/test_hooks_*.py` fed with real captured fixtures from Phase 0

### Phase 7 — Registration
- [ ] Add `logging` + `hooks` keys to `.claude/settings.json`

### Phase 8 — Manual smoke test
- [ ] Fresh session: confirm log + buffer files appear on SessionStart
- [ ] One-edit turn: confirm single JSONL line, correct refs.commit/files
- [ ] Resume same session: confirm append, not recreate
- [ ] Multi-tool-call turn: confirm one line, all tool names, one
      summarization call

### Phase 9 — Backlog housekeeping
- [x] BACKLOG.md already created (done pre-branch, on `dev`)

## Verification commands
```
pytest tests/ -v
```
Manual smoke test steps are listed in PLAN.md's Verification section.
