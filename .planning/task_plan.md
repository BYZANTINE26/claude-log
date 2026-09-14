# Task Plan: claude-log Publish

## Goal
Close out `BACKLOG.md`'s `## Publish` section (`#13`-`#20`) on branch
`feature/publish-plugin`, per `.claude/plans/PLAN.md`'s Publish phase, so
claude-log can be installed by a stranger through Claude Code's own
plugin mechanism.

## Next Step
All planned phases done. Confirm with the user before merging into `dev`.

## Current Phase
Phase 7 (done)

## Phases
Copied from `.claude/plans/PLAN.md`'s Publish "Order of implementation".

### Phase 1: Manifest + license (`#14`)
- [x] Add `repository`, `homepage`, `license`, `keywords` to
      `.claude-plugin/plugin.json`
- [x] Add a real `LICENSE` file (MIT)
- [x] `claude plugin validate . --strict` passes clean
- **Status:** done

### Phase 2: Cross-platform hook invocation (`#15`)
- [x] Switch `hooks/hooks.json` to exec form (`command`/`args`)
- [x] Decided: document `python3` on `PATH` as a hard prerequisite
      (no auto-detection — untestable on a real Windows machine here)
- [x] Real headless run still logs a correct entry after the switch
- **Status:** done

### Phase 3: File locking (`#16`, elevates `#1`)
- [x] Advisory lock (`logger._locked`) around `logger.append_entry` and
      the `.state` read-modify-write (`fcntl` POSIX, `msvcrt` Windows)
- [x] Test: two concurrent writers, log ends up with both entries intact
- [x] Test: direct lock-primitive test against a read-then-write race
      (fails without the fix: 5/50 increments, confirming it's real)
- **Status:** done

### Phase 4: Marketplace distribution (`#13`)
- [x] `.claude-plugin/marketplace.json` with a `github` source (no
      explicit `ref` — resolves to the repo's default branch, per the
      decision that everything lands on `main` once ready to ship)
- [x] Real `claude plugin marketplace add` + `claude plugin install` test
      in a throwaway project, not just `--plugin-dir`
- **Status:** done

### Phase 5: Claude-as-summarizer provider (`#20`)
- [x] Spike: confirmed `claude -p ... --safe-mode --tools ""` neither
      triggers claude-log's own hooks nor executes a tool call (zero
      internal.log activity even with --plugin-dir pointing at
      claude-log itself)
- [x] `"provider": "claude-code"` config shape, additive to (not
      replacing) the OpenAI-compatible path
- [x] `MAX_THINKING_TOKENS=0` in the subprocess environment; warns
      rather than silently ignoring the Fable-model exception
- [x] Any Claude model id accepted, not hardcoded to Haiku
- [x] Real end-to-end verification through the actual hook pipeline:
      genuine summary, one clean hook cycle, no recursion
- **Status:** done

### Phase 6: README pass for installers (`#19`, folds in `#18`)
- [x] Marketplace-install quickstart
- [x] Plain-language "what does this do to my machine" section
- [x] First-run troubleshooting (`#15`'s gap, no endpoint configured)
- [x] License/repo links; note that uninstall doesn't clean up
      `~/.claude-log/` (`#18`); document `#20`'s opt-in provider
- **Status:** done

### Phase 7: Cross-platform testing (`#17`)
- [x] Full 65-test unit suite verified on real Linux (Docker,
      python:3.12-slim) — real evidence, not assumed, for the
      `fcntl`-based locking and git subprocess calls
- [x] Confirmed the `claude` CLI installs cleanly in a Linux container
      too; decided against a full headless run there (would need
      personal auth credentials in a throwaway container)
- [x] Windows documented as an honest, still-open gap (`#17` narrowed,
      not closed) — no Windows container path available here
- **Status:** done

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Branch scoped to exactly `BACKLOG.md`'s Publish tickets (`#13`-`#20`) | `#20` was initially mis-scoped as unrelated, but it sits physically inside `## Publish` — corrected. `#5`/`#6`/`#10`/`#11` are unrelated or still-open research, genuinely out of scope |
| Phase order: `#14` -> `#15` -> `#16` -> `#13` -> `#20` -> `#19` -> `#17` | Real dependency order — manifest/license first (nothing depends on it), hook portability before anything documents/distributes the install path, file locking as an independent correctness fix, marketplace once the install path is correct, `#20` once the plugin's install/correctness story is solid, README once both the marketplace path and `#20` are real, cross-platform testing last |

## Errors Encountered
| Error | Resolution |
|-------|------------|
