# Task Plan: claude-log Publish

## Goal
Close out `BACKLOG.md`'s `## Publish` section (`#13`-`#19`) on branch
`feature/publish-plugin`, per `.claude/plans/PLAN.md`'s Publish phase, so
claude-log can be installed by a stranger through Claude Code's own
plugin mechanism.

## Next Step
Start Phase 1 — manifest metadata + LICENSE (`#14`).

## Current Phase
Phase 1

## Phases
Copied from `.claude/plans/PLAN.md`'s Publish "Order of implementation".

### Phase 1: Manifest + license (`#14`)
- [ ] Add `repository`, `homepage`, `license`, `keywords` to
      `.claude-plugin/plugin.json`
- [ ] Add a real `LICENSE` file
- [ ] `claude plugin validate . --strict` passes clean
- **Status:** pending

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

### Phase 5: README pass for installers (`#19`, folds in `#18`)
- [ ] Marketplace-install quickstart
- [ ] Plain-language "what does this do to my machine" section
- [ ] First-run troubleshooting (`#15`'s gap, no endpoint configured)
- [ ] License/repo links; note that uninstall doesn't clean up
      `~/.claude-log/` (`#18`)
- **Status:** pending

### Phase 6: Cross-platform testing (`#17`)
- [ ] Verify everywhere this environment allows
- [ ] Document any genuinely untestable case (e.g. real Windows) as an
      honest, named gap rather than assumed fixed
- **Status:** pending

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Branch scoped to exactly `BACKLOG.md`'s Publish tickets (`#13`-`#19`) | `#5`/`#6`/`#10`/`#11`/`#20` are unrelated or still-open research, not part of "ship as a production plugin" |
| Phase order: `#14` -> `#15` -> `#16` -> `#13` -> `#19` -> `#17` | Real dependency order — manifest/license first (nothing depends on it), hook portability before anything documents/distributes the install path, file locking as an independent correctness fix, marketplace once the install path is correct, README once the marketplace path is real, cross-platform testing last |

## Errors Encountered
| Error | Resolution |
|-------|------------|
