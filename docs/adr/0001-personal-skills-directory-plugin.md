---
Status: accepted
---

# Distribute claude-log as a personal skills-directory plugin

claude-log must work on any project on the machine without per-project
setup. A personal skills-directory plugin (`~/.claude/skills/claude-log/`,
loaded via `claude plugin init`) auto-registers its hooks for every
project a user opens, with no marketplace listing, install step, or
per-project `.claude/settings.json` edits. A marketplace plugin would add
shareability we don't need yet; per-project hook registration (the
scrapped branch's approach) requires manual setup on every new project,
defeating the "works right off the back" goal.

## Considered Options
- Marketplace-distributed plugin — shareable, but requires `plugin.json`
  versioning and a marketplace listing before it's usable anywhere.
- Per-project `.claude/settings.json` hook registration (original
  approach) — works, but must be redone by hand for every project.

## Consequences
Sharing claude-log with someone else later just means pointing a
marketplace at the same `hooks/hooks.json` structure — not a rewrite.
