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
