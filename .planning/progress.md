# Progress Log

## Session: 2026-09-13

### Current Status
- **Phase:** 7 - Cross-platform testing (`#17`) — done, all phases complete
- **Started:** 2026-09-13

### Actions Taken
- Branch `feature/publish-plugin` created off `dev`, `BRANCH.md`
  committed.
- Added a "Plan: Publish" section to `.claude/plans/PLAN.md`, sequencing
  `BACKLOG.md`'s `#13`-`#19` by real dependency order.
- Ran `planning-with-files:planning-with-files`'s `init-session.sh`;
  moved its output into `.planning/` (replacing the prior branch's
  Core Logging planning docs, since each branch gets isolated planning
  files) and populated it with this branch's real phases from
  `PLAN.md`.
- Corrected scope: `#20` is physically inside `BACKLOG.md`'s `## Publish`
  section (it was appended after `#19` but before checking the section
  header's actual position) — added as Phase 5, README (now Phase 6)
  updated to also document it, cross-platform testing pushed to Phase 7.
- Phase 1 done: added `repository`/`homepage`/`license`/`keywords` to
  `.claude-plugin/plugin.json` and a real MIT `LICENSE` file.
  `claude plugin validate . --strict` passes clean with no
  unrecognized-field warnings.
- Phase 2 done: `hooks/hooks.json` switched to exec form
  (`command: "python3"`, `args: [...]`) for all five hooks. Verified
  with a real headless run — correct log entry, full hook trace in
  `internal.log`. Documented `python3` on `PATH` as a hard prerequisite
  in `README.md`, including the concrete Windows gap (python.org
  installs don't provide a `python3` executable), since a real Windows
  test isn't possible in this environment — no interpreter
  auto-detection built, by explicit decision.
- Phase 3 done: added `logger._locked()`, an advisory OS-level lock
  (`fcntl.flock` POSIX, `msvcrt.locking` Windows) around `append_entry`
  and the `.state` read-modify-write (`mark_context_reset`,
  `record_reingestion`). Two tests: a direct lock-primitive test against
  a classic read-then-write race (proven meaningful — fails without the
  fix, 5/50 increments lost), and a concurrent-writers test against
  `append_entry` with large entries. Full suite 60/60. Verified with a
  real headless run — correct log entry, `.jsonl.lock` file created
  alongside the log as expected. Removed both `#1` and `#16` from
  `BACKLOG.md`.
- Phase 4 done: added `.claude-plugin/marketplace.json`. Real test via
  `claude plugin marketplace add BYZANTINE26/claude-log@feature/publish-plugin`
  + `claude plugin install claude-log@claude-log` in a fresh throwaway
  project — both succeeded mechanically. Found a real, confirmed gap:
  the marketplace's own `@ref` only pins where `marketplace.json` itself
  is fetched from; each plugin entry's own `source` (no `ref` set)
  independently resolves to the repo's default branch, `main`, which
  today only has the original pre-implementation commit — confirmed via
  `claude plugin list` showing the installed version pinned to `main`'s
  commit SHA, with no hooks firing as a direct, correct consequence (not
  a bug). Per explicit user decision, no `ref` was added to work around
  this — resolved instead by shipping everything to `main` once ready,
  at which point the same mechanism works with no special-casing.
  Verified the install *mechanism* itself works via a temporary,
  never-committed local pin to `feature/publish-plugin`'s ref, reverted
  before committing anything. Cleaned up the test marketplace/plugin
  registration and `~/.claude/settings.json` afterward. Removed `#13`
  from `BACKLOG.md`.
- Phase 5 done: added `summarizer.call_claude_code_provider()` for
  `"provider": "claude-code"`. Two spikes run before writing any
  production code: (1) `--safe-mode --tools ""` with `--plugin-dir`
  pointing at claude-log itself produced zero `internal.log` activity —
  confirmed recursion-free, not assumed; (2) the full command shape
  (`claude -p ... --output-format json --json-schema ... --safe-mode
  --tools ""`, `MAX_THINKING_TOKENS=0`) returns a correct
  `structured_output.summary` with `thinking_tokens: 0`. 6 unit tests
  (mocked subprocess). Then a real end-to-end run through the actual
  hook pipeline with the provider genuinely configured: a real
  (non-`summary_failed`) summary, one clean hook cycle in
  `internal.log`, no recursion. Full suite 65/65. Removed `#20` from
  `BACKLOG.md`.
- Phase 6 done: rewrote `README.md`'s Installation/Configuration/Where
  Things Live sections and added two new ones ("What This Does to Your
  Machine", "First-Run Troubleshooting"). Real marketplace-install
  quickstart replaces `--plugin-dir` as the primary path (kept as an
  "Alternative: load without installing" option). Both
  `summarization_endpoint` shapes documented side by side, including the
  new `claude-code` provider. Added a License section and the `#18`
  uninstall/`${CLAUDE_PLUGIN_DATA}` note. Full suite still 65/65, both
  manifests still validate clean. Removed `#19` and `#18` from
  `BACKLOG.md`.
- Phase 7 done: ran the full 65-test unit suite inside a real Linux
  container (Docker, `python:3.12-slim`) — genuine evidence for the
  `fcntl`-based file locking, git subprocess calls, and path handling on
  a different kernel/filesystem than the macOS this project was
  developed on. Confirmed the `claude` CLI installs cleanly in a Linux
  container too; decided against a full headless run there, since it
  would require placing personal auth credentials in a throwaway
  container for marginal extra confidence beyond what the unit suite
  already covers. Windows remains genuinely untested — no Windows
  container path available in this environment. Narrowed `#17` in
  `BACKLOG.md` from "no cross-platform testing at all" to "Windows
  specifically," rather than closing it outright. This was the last
  planned phase — all of `BACKLOG.md`'s `## Publish` section (`#13`-
  `#20`) is now resolved except `#17` (narrowed, not closed) and `#21`
  (split out, genuinely separate, still open).

### Test Results
| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Full suite (60 tests) | all pass | all pass | ✅ |
| Lock-primitive race test, unlocked (sanity check) | fails | failed (5/50) | ✅ proves the test is meaningful |
| Full suite (65 tests, Claude-as-summarizer added) | all pass | all pass | ✅ |
| Full suite on real Linux (Docker, python:3.12-slim) | all pass | all pass | ✅ |

### Errors
| Error | Resolution |
|-------|------------|
