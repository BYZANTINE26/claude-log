# Findings & Decisions

## Requirements
- Scope is exactly `BACKLOG.md`'s `## Publish` section, `#13`-`#20` —
  see that section for the full research behind each ticket (already
  grounded in `plugins.md`, `plugin-marketplaces.md`,
  `plugins-reference.md`, `hooks.md`, and `model-config.md`, fetched
  directly). This branch implements/resolves those tickets; it doesn't
  re-derive the research.
- `#10`/`#11` (open research items unrelated to publishing) are
  explicitly out of scope. `#20` was initially left off by mistake — it
  is physically inside `## Publish`, so it's in scope (corrected
  2026-09-13, see `task_plan.md`'s Decisions Made).

## Research Findings
- `/plugin marketplace add ...` fails headless (`-p`) with "`/plugin`
  isn't available in this environment" — the non-interactive equivalent
  is the top-level `claude plugin marketplace add`/`claude plugin
  install` CLI subcommands (confirmed working), not the slash command
  under `-p`.
- **Real, confirmed gap**: the GitHub repo's default branch is `main`,
  which per this project's convention only ever holds the original
  pre-implementation commit — no plugin code. `claude plugin
  marketplace add owner/repo@ref` lets you pin *which branch the
  marketplace repo itself is cloned from*, but each plugin *entry*'s own
  `source` (ours has no `ref`) resolves **independently** to the repo's
  default branch regardless of the marketplace's own ref. Confirmed
  live: after adding the marketplace pinned to `@feature/publish-plugin`
  and installing, `claude plugin list` showed `Version: 87253f697a19` —
  `main`'s single initial commit SHA, not this branch's code. Installing
  correctly surfaced no hooks, because `main` genuinely has none yet;
  this isn't a bug in the mechanism, just accurate given `main`'s real
  content today.
- Per explicit user decision: no `ref` is added to `marketplace.json`
  (rejected pinning to `dev` or documenting `@dev`) — the resolution is
  that everything will be pushed to `main` once the project is ready to
  ship, at which point the same mechanism resolves correctly with no
  special-casing needed.
- Verified the install *mechanism* itself works correctly end-to-end
  (marketplace add, plugin install, correct version-SHA resolution)
  using a temporary, never-committed local edit pinning the plugin
  entry's `source.ref` to `feature/publish-plugin` — reverted before
  committing anything, not pushed, since the real fix (ship to `main`)
  is a repo-content change, not a marketplace.json change.
- `claude plugin validate .` validates whichever manifest it finds in
  `.claude-plugin/` — once `marketplace.json` was added alongside
  `plugin.json` in the same directory, `validate .` switched to
  reporting "Validating marketplace manifest" instead of "Validating
  plugin manifest". `plugin.json` was already confirmed clean in Phase 1
  before `marketplace.json` existed and hasn't changed since.

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Phase order `#14` -> `#15` -> `#16` -> `#13` -> `#19` -> `#17` | See `task_plan.md`'s Decisions Made — real dependency order, not ticket-number order |

## Issues Encountered
| Issue | Resolution |
|-------|------------|

## Resources
- `.claude/plans/PLAN.md`'s "Plan: Publish (feature/publish-plugin)"
  section — this branch's single source of truth for phase order
- `BACKLOG.md`'s `## Publish` section — scope and full research per
  ticket
