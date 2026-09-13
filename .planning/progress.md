# Progress Log

## Session: 2026-09-13

### Current Status
- **Phase:** 9 - Docs (done)
- **Started:** 2026-09-13

### Actions Taken
- Branch `feature/core-logging` created off `dev`, `BRANCH.md` committed.
- Corrected `SessionEnd`/`MessageDisplay` field-name research from a
  summary-table pass to the real per-event docs sections; fixed
  `SPEC.md`, `docs/specs/core-logging.md`, `docs/adr/0007`, `PLAN.md`.
- Documented that a resumed session gets the full recent-context window
  immediately, with no `/claude-log-load` needed — only `/clear` gates it.
- Ran `planning-with-files:planning-with-files`'s `init-session.sh`;
  moved its output into `.planning/` and populated it with this
  branch's real phases from `PLAN.md`.
- Phase 0 (remaining field-name ambiguity) closed — see findings.md.
- Phase 1 (`config.py`) done: settings load, path resolution, rotating
  internal logger, 7 unit tests passing.
- Phase 2 (`git_snapshot.py`) done: hash-diff file-touch tracking, 9
  unit tests passing, one real bug found and fixed (see findings.md).
- Phase 3 (`buffer.py`) done: per-turn buffer, MessageDisplay delta
  accumulation, orphan sweep, 8 unit tests passing.
- Phase 4 (`logger.py`) done: JSONL log, marker-entry building, the
  context-reset window formula (all ADR-0007 scenarios), 11 unit tests
  passing.
- Phase 5 (`summarizer.py`) done: OpenAI-compatible endpoint call, no
  rule-based fallback, 7 unit tests passing against a local http.server.
- Corrected two more field-name errors ahead of Phase 6: UserPromptSubmit's
  field is `prompt` not `user_prompt`; confirmed directly (not just
  inferred) that `Stop` never fires on a Ctrl+C interrupt, closing part
  of the open research ticket.
- Phase 6 done: all five hooks, `_hook_io.py`, and the
  `/claude-log-load` skill (`claude_log/cli.py`) implemented; 22
  integration tests passing.
- Phase 7 done: `.claude-plugin/plugin.json` + `hooks/hooks.json`
  assembled, `claude plugin validate .` passes clean, and a real headless
  run (`claude --plugin-dir . -p "..."`) produced a correct end-to-end
  log entry (real prompt_id as turn_id, correct commit snapshots, empty
  files list, summary_failed marker since no endpoint is configured yet,
  buffer cleaned up afterward). This is real evidence, not a guess —
  self-hosting caught the same class of real bugs it caught last time.
- Phase 8 done: full real-world test run against a fresh test project
  (`/Volumes/GBC/projects/test_claude_log`), delegated to a subagent,
  covering every PLAN.md Verification scenario plus the queued-prompt
  research question. 7/8 passed; 1 found a real bug (see findings.md) —
  fixed in `git_snapshot.py`, regression test added, 57/57 suite passing.
  Follow-up confirmed a real summarization endpoint produces genuine
  summaries end-to-end.
- Phase 9 done: `README.md` rewritten from its pre-implementation
  planning-phase state to describe the shipped plugin (installation,
  configuration, file layout, gitignore note); `CHANGELOG.md` created
  (0.1.0). Ran an independent full re-test (subagent, fresh throwaway
  project `test_claude_log_v2`) confirming the `git_snapshot.py` fix
  holds — the exact regression shape (untracked directory + unrelated
  tracked-file edit in one turn) now correctly reports all touched files.
  All 9 scenarios passed; the `files: []` anomaly still did not
  reproduce (now two independent non-reproduction attempts, see
  findings.md); zero errors in claude-log's own internal log across the
  run.

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| `tests/test_config.py` (7 tests) | all pass | all pass | ✅ |
| `tests/test_git_snapshot.py` (9 tests) | all pass | all pass | ✅ |
| `tests/test_buffer.py` (8 tests) | all pass | all pass | ✅ |
| `tests/test_logger.py` (11 tests) | all pass | all pass | ✅ |
| `tests/test_summarizer.py` (7 tests) | all pass | all pass | ✅ |
| Hook + CLI integration tests (22 tests) | all pass | all pass | ✅ |
| `test_untracked_directory_does_not_blank_out_other_files` (regression) | pass | pass | ✅ |
| Full suite | 57/57 | 57/57 | ✅ |
| Real end-to-end test run (headless, 8 scenarios) | 8/8 pass | 7/8 pass, 1 bug found+fixed | ✅ (post-fix) |
| Independent re-test post-fix (headless, 9 scenarios incl. regression re-check) | 9/9 pass | 9/9 pass | ✅ |

### Errors
| Error | Resolution |
|-------|------------|
