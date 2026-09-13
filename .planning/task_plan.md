# Task Plan: claude-log Core Logging implementation

## Goal
Implement claude-log's Core Logging as a personal Claude Code plugin,
per `.claude/plans/PLAN.md` and `docs/adr/0001`-`0007`, on branch
`feature/core-logging`.

## Next Step
Write `claude_log/git_snapshot.py` (commit hash + hashed dirty-file map).

## Current Phase
Phase 2

## Phases
Copied from `.claude/plans/PLAN.md`'s Order of implementation.

### Phase 0: Remaining field-name ambiguity
- [x] Confirm all five hooks' real input fields directly from the hooks
      reference's per-event sections (not just the summary table)
- [x] Narrow the one open ambiguity (`prompt_id` vs. `turn_id` on
      `MessageDisplay`) to a defensive `.get()` fallback, verified later
      in the manual smoke test, not blocking
- **Status:** done

### Phase 1: `config.py`
- [x] `DEFAULT_CONFIG`, `load_config()` — reads `~/.claude-log/config.json`
- [x] Path resolution: `plugin_home`, `project_log_dir`, `log_file_path`,
      `buffer_path`, `state_path`
- [x] `get_logger()` — rotating internal log, level from config
- [x] Unit tests (7, all passing)
- **Status:** done

### Phase 2: `git_snapshot.py`
- [ ] `snapshot_git_state()` — commit hash + hashed dirty-file map
- [ ] `files_touched()` — commit-diff union hash-diff, per ADR-0004
- [ ] Unit tests, including the pre-existing-dirty-file exclusion case
- **Status:** in_progress

### Phase 3: `buffer.py`
- [ ] `start_turn`, `append_assistant_message`, `read_and_clear`
- [ ] `sweep_orphaned` — `turn_lost` markers, per ADR-0006
- [ ] Unit tests, atomic round-trip + orphan sweep
- **Status:** pending

### Phase 4: `logger.py`
- [ ] `initialize_or_resume`, `append_entry`, `build_entry`
- [ ] `get_recent_entries` with the window-size formula (ADR-0007)
- [ ] `mark_context_reset`, `record_reingestion`
- [ ] Unit tests: reset/no-reset/re-ingestion scenarios, resume uses
      full window
- **Status:** pending

### Phase 5: `summarizer.py`
- [ ] `summarize()`, `call_openai_compatible_endpoint()`
- [ ] Unit tests against a local `http.server` fixture: success,
      timeout, malformed-response (all three → `summary_failed`)
- **Status:** pending

### Phase 6: Hooks + `claude-log-load` skill
- [ ] `hooks/_hook_io.py`
- [ ] `hooks/{session_start,user_prompt_submit,message_display,stop,
      session_end}.py`, each directly executable
- [ ] `skills/claude-log-load/SKILL.md`
- [ ] Hook sequence integration tests via canned fixtures, including an
      interrupted-turn scenario
- **Status:** pending

### Phase 7: Plugin assembly
- [ ] `.claude-plugin/plugin.json`, `hooks/hooks.json`
- [ ] Local test via `claude --plugin-dir`
- **Status:** pending

### Phase 8: Manual smoke test
- [ ] Fresh session, resume, `/clear`, `/claude-log-load`, interrupt —
      see `.claude/plans/PLAN.md`'s Verification section
- **Status:** pending

### Phase 9: Docs
- [ ] Update `BACKLOG.md`, `CHANGELOG.md`, `README.md`
- **Status:** pending

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Used `planning-with-files:planning-with-files` skill for real this session | Plugin loaded after a `/reload-plugins`; a quick manual read of its shell scripts found no network calls or eval-style patterns, given `skillspector` is still unavailable to run the full scan |

## Errors Encountered
| Error | Resolution |
|-------|------------|
