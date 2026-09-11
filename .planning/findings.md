# Findings

Durable discoveries and decisions made during execution of the Core Logging
MVP, recorded as they happen (per CLAUDE.md subagent-delegation rules).

## 2026-09-11 — planning-with-files plugin not usable
`/pwf` and `/plan` commands from the `planning-with-files` plugin don't
load in this session despite `enabledPlugins` in `.claude/settings.json`.
Global `~/.claude/settings.json` doesn't list it as enabled either, and the
`skillspector` MCP tool (needed to scan it per CLAUDE.md's
before-installing-any-skill rule) is also not loaded. The plugin's own
description contains unusually defensive language ("never runs commands
declared in Markdown", "No network upload path" repeated) for a
planning-templates package that also ships hooks — treated as a reason to
NOT troubleshoot further without a scan. Decision: build `.planning/`
files manually (this directory), matching the plugin's intended output
shape, without installing/relying on its hooks.

## 2026-09-11 — Claude Code hook JSON contract used (unverified live)
No live Claude Code session was available to capture ground-truth hook
stdin payloads (Phase 0 of task_plan.md called for this). Implemented
against the following best-known contract instead, with defensive
`.get()`-based access everywhere so a wrong field name degrades to a
generic fallback rather than crashing the hook:
- All hooks: `session_id`, `transcript_path`, `cwd`, `hook_event_name`
- SessionStart: `source` ("startup" | "resume" | "clear")
- UserPromptSubmit: `prompt`
- PostToolUse: `tool_name`, `tool_input`, `tool_response`
- Stop: `stop_hook_active`

**Follow-up required**: run the manual smoke test in PLAN.md's
Verification section against a real Claude Code session to confirm these
field names, and adjust `hooks/_hook_io.py` extraction points if they
differ. This is the single biggest risk item carried out of this
implementation pass.
