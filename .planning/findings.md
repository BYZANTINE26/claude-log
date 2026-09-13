# Findings & Decisions

## Requirements
- Full design settled via `grill-with-docs` on `dev` before this branch:
  `INTENT.md`, `SPEC.md`, `docs/specs/core-logging.md`,
  `docs/adr/0001`-`0007`, `.claude/plans/PLAN.md`. This branch implements
  that design; it does not re-derive it.

## Research Findings
- All five hooks' real input fields confirmed directly from
  `code.claude.com/docs/en/hooks.md`'s per-event sections (fetched via
  `curl` + `grep`/`sed`, not the summary-table pass used earlier, which
  had mis-stated `SessionEnd`'s field as `end_reason` instead of the
  real `reason`).
- `MessageDisplay` delivers `delta` incrementally per batch in
  interactive sessions (`index`, `final` track progress), and once in
  full for non-interactive/SDK runs. One remaining ambiguity: its
  documented example doesn't show `prompt_id` alongside its own
  `turn_id` — hook code reads both defensively, verified live during
  the Phase 8 manual smoke test.
- A resumed session (`SessionStart` `source: "resume"`) never gets a
  context-reset marker, so `get_recent_entries`' window formula
  naturally falls back to the full configured window with no extra
  code path needed — documented explicitly in `SPEC.md`/
  `docs/specs/core-logging.md` so this guarantee isn't accidentally
  broken later.
- `SessionEnd` also fires with `reason: "clear"` or `"resume"`, not only
  true termination — the orphan sweep runs unconditionally regardless of
  `reason`, so this doesn't change the design (see ADR-0007).

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| `bin/` wrapper scripts and `paths.py`/`session_state.py`/`internal_log.py` dropped from `PLAN.md`'s layout | Ponytail review: `bin/` was boilerplate for a per-project `PYTHONPATH` problem the plugin architecture (ADR-0001) already solves; the other three were single-caller, near-one-line modules that didn't earn a separate file — merged into `config.py`/`logger.py` |
| `planning-with-files:planning-with-files` used for real this session | Plugin loaded after the user ran `/reload-plugins`; `skillspector` still unavailable to run the full pre-trust scan, so a manual read of its shell scripts (no network calls, no eval-style patterns) stood in as a lighter-weight check, at the user's explicit direction |

- `UserPromptSubmit`'s real field is `prompt`, not `user_prompt` — a
  second error from the original summary-table research pass (the first
  was `SessionEnd`'s `end_reason` vs. real `reason`). Both now fixed in
  `docs/specs/core-logging.md` before any hook code was written against
  them.
- `Stop`'s own per-event doc section states outright: "Does not run if
  the stoppage occurred due to a user interrupt." This confirms (not
  just designs defensively for) the need for ADR-0006's `turn_lost`
  orphan sweep — every interrupted turn hits this path, not a
  hypothetical edge case. Only the queued-prompt sequencing question
  remains genuinely open (see `research` ticket in `BACKLOG.md`).

## Real end-to-end test run (2026-09-13, subagent-delegated)
Ran against a fresh test project (`/Volumes/GBC/projects/test_claude_log`),
headless `claude --plugin-dir /Volumes/GBC/projects/claude-log --model
claude-haiku-4-5-20251001 -p ...`/`--resume`, covering every scenario in
`.claude/plans/PLAN.md`'s Verification section plus the open research
question. 7 of 8 scenarios passed cleanly (start+one turn, multi-turn
resume growth, resume-never-writes-a-reset-marker, `/clear` genuinely
triggers a reset marker via headless `-p "/clear"`, `/claude-log-load`
via its plugin-qualified command name, `/compact` doesn't disturb state,
and an interrupted turn via SIGINT correctly produces a `turn_lost`
marker through the `SessionEnd` sweep path).

**Real bug found and fixed**: `git_snapshot.py::_hash_paths` silently
emptied the *entire* dirty-hash map for a snapshot whenever any wholly
untracked directory existed in the working tree (e.g. claude-log's own
`.claude-log/.state/`, created by the `/clear` test itself) — because
`git status --porcelain` folds an untracked directory into one
unhashable line, and the single batched `git hash-object` call over all
dirty paths fails outright on it, with `_run()`'s failure-swallowing
silently discarding every other path's hash too, not just the
directory's. Fixed with `--untracked-files=all` on the status call plus
an `os.path.isfile` filter before hashing (defense in depth for
submodule-like paths `--untracked-files=all` doesn't expand). Added
`test_untracked_directory_does_not_blank_out_other_files` as a permanent
regression test. See `CHANGELOG.md` and the commit for full detail.

**Two items left genuinely open** (moved to `BACKLOG.md`): a single
`files: []` result on a real edit-only turn that could not be reproduced
in 3 follow-up attempts (predates the directory bug, unexplained); and
the queued-prompt research question, only partially exercised (two
concurrent `--resume` calls showed no corruption, but that's not proof
of the interactive "prompt queued mid-generation" scenario specifically).

**Also confirmed**: after the test run, a real summarization endpoint
was configured in `~/.claude-log/config.json` and two further turns
produced genuine, accurate `summary` text instead of `summary_failed` —
the full pipeline (buffer -> git snapshot -> summarizer HTTP call ->
log entry) works end-to-end with a real model.

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| `init-session.sh` created `task_plan.md`/`findings.md`/`progress.md` at the repo root, not `.planning/` | Moved into `.planning/` by hand to match this project's CLAUDE.md convention |
| A blanket `.strip()` on `git status --porcelain`'s output ate the leading space that distinguishes " D file" (unstaged delete) from other status codes, corrupting the first parsed path | Switched `_run()` to a trailing-only `.rstrip("\n")`; caught by `test_deleted_file_is_included` and the modified-pre-existing-dirty-file test both failing with a mangled path |
| PLAN.md's `git_snapshot.py` sketch took `commit_before, commit_after, dirty_before, dirty_after` as four separate parameters | Simplified `files_touched()` to take the two whole snapshot dicts instead — same data, one parameter each, less to keep in sync at call sites |

## Resources
- `.claude/plans/PLAN.md` — master implementation plan (this branch's
  single source of truth for phases/order)
- `docs/adr/0001` through `0007` — architectural decisions this
  implementation must match
- `BACKLOG.md` — everything explicitly out of scope for this branch
