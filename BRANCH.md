# Branch: feature/publish-plugin

## Purpose
Work through every ticket in `BACKLOG.md`'s `## Publish` section (`#13`-
`#19`), so claude-log can be installed by a stranger through Claude Code's
own plugin mechanism, not just loaded via `--plugin-dir` or hand-cloned
into `~/.claude/skills/`.

## Scope (tickets this branch closes or advances)
- `#14` — `plugin.json` metadata (`repository`, `homepage`, `license`,
  `keywords`) + a real `LICENSE` file.
- `#15` — cross-platform hook invocation (exec form, Windows `python3`
  gap).
- `#16` — file locking on the session log (elevates `#1`).
- `#13` — `.claude-plugin/marketplace.json` + a real marketplace-install
  test.
- `#19` — README pass aimed at a first-time plugin installer.
- `#17` — cross-platform testing, to whatever extent this environment
  allows (documented honestly if a real Windows/Linux run isn't
  possible here).
- `#18` — README note that `${CLAUDE_PLUGIN_DATA}` isn't used, so
  uninstall doesn't clean up `~/.claude-log/`.

Not in scope: `#5`/`#6` (local model, benchmarking), `#10`/`#11`/`#20`
(open research and the Claude-as-summarizer feature) — those stay parked.

## Not merged
This file is unique to this branch and is dropped before merging into
`dev`, per the project's git workflow conventions.
