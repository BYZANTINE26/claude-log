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
(To be filled in per-phase as real findings surface — e.g. how
`claude plugin validate --strict` reacts to the new manifest fields,
what Windows-specific behavior is confirmed vs. assumed for `#15`, and
what a real `/plugin marketplace add` test in a throwaway project
reveals for `#13`.)

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
