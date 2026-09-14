# Task Plan: claude-log Publish

## Goal
Close out `BACKLOG.md`'s `## Publish` section (`#13`-`#20`) on branch
`feature/publish-plugin`, per `.claude/plans/PLAN.md`'s Publish phase, so
claude-log can be installed by a stranger through Claude Code's own
plugin mechanism.

## Next Step
Start Phase 2 — cross-platform hook invocation (`#15`).

## Current Phase
Phase 2

## Phases
Copied from `.claude/plans/PLAN.md`'s Publish "Order of implementation".

### Phase 1: Manifest + license (`#14`)
- [x] Add `repository`, `homepage`, `license`, `keywords` to
      `.claude-plugin/plugin.json`
- [x] Add a real `LICENSE` file (MIT)
- [x] `claude plugin validate . --strict` passes clean
- **Status:** done

### Phase 2: Cross-platform hook invocation (`#15`)
- [ ] Switch `hooks/hooks.json` to exec form (`command`/`args`)
- [ ] Decide and implement the Windows `python3`-vs-`python` handling
- [ ] Real headless run still logs a correct entry after the switch
- **Status:** pending

### Phase 3: File locking (`#16`, elevates `#1`)
- [ ] Advisory lock around `logger.append_entry` and the `.state`
      read-modify-write (`fcntl` POSIX, `msvcrt` Windows)
- [ ] Test: two concurrent writers, log ends up with both entries intact
- **Status:** pending

### Phase 4: Marketplace distribution (`#13`)
- [ ] `.claude-plugin/marketplace.json` with a `github` source
- [ ] Real `/plugin marketplace add` + `/plugin install` test in a
      throwaway project, not just `--plugin-dir`
- **Status:** pending

### Phase 5: Claude-as-summarizer provider (`#20`)
- [ ] Spike: confirm `claude -p ... --safe-mode --tools ""` neither
      triggers claude-log's own hooks nor executes a tool call
- [ ] `"provider": "claude-code"` config shape, additive to (not
      replacing) the OpenAI-compatible path
- [ ] `MAX_THINKING_TOKENS=0` in the subprocess environment; surface the
      Fable-model exception rather than silently ignoring it
- [ ] Any Claude model id accepted, not hardcoded to Haiku
- **Status:** pending

### Phase 6: README pass for installers (`#19`, folds in `#18`)
- [ ] Marketplace-install quickstart
- [ ] Plain-language "what does this do to my machine" section
- [ ] First-run troubleshooting (`#15`'s gap, no endpoint configured)
- [ ] License/repo links; note that uninstall doesn't clean up
      `~/.claude-log/` (`#18`); document `#20`'s opt-in provider
- **Status:** pending

### Phase 7: Cross-platform testing (`#17`)
- [ ] Verify everywhere this environment allows
- [ ] Document any genuinely untestable case (e.g. real Windows) as an
      honest, named gap rather than assumed fixed
- **Status:** pending

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Branch scoped to exactly `BACKLOG.md`'s Publish tickets (`#13`-`#20`) | `#20` was initially mis-scoped as unrelated, but it sits physically inside `## Publish` — corrected. `#5`/`#6`/`#10`/`#11` are unrelated or still-open research, genuinely out of scope |
| Phase order: `#14` -> `#15` -> `#16` -> `#13` -> `#20` -> `#19` -> `#17` | Real dependency order — manifest/license first (nothing depends on it), hook portability before anything documents/distributes the install path, file locking as an independent correctness fix, marketplace once the install path is correct, `#20` once the plugin's install/correctness story is solid, README once both the marketplace path and `#20` are real, cross-platform testing last |

## Errors Encountered
| Error | Resolution |
|-------|------------|
