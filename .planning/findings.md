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

## 2026-09-11 — settings.json rejects arbitrary top-level keys
Attempted to add a "logging" key to `.claude/settings.json` per
docs/specs/core-logging.md's original Configuration section. Claude Code
validates settings.json against a strict schema and rejected it
("Unrecognized field: logging"); only "hooks" (among the keys this project
needs) is a real settings.json field. Decision: claude-log's own config
now lives in `.claude/claude_log_config.json`, a separate file
`config.py` reads directly. `.claude/settings.json` carries only the
`hooks` registration. SPEC.md and docs/specs/core-logging.md updated to
match.

## 2026-09-11 — real hook payloads captured live, contract confirmed
Once hooks were registered in this project's own `.claude/settings.json`,
they fired for real during this very implementation session (this project
is its own first user). Found a genuine
`.claude/logs/.buffers/session_<real-session-id>.json` populated by actual
PostToolUse calls. Confirms:
- `cwd`, `session_id`, `tool_name`, `tool_input` field names are all
  correct as assumed — `tool_input.file_path` (snake_case) matched real
  Edit/Write payloads exactly.
- `tool_response` for Edit/Write arrives as a **dict**, not a string, and
  contains the entire old/new file content (keys like `type`, `filePath`
  [camelCase here, unlike tool_input's snake_case], `oldString`,
  `newString`). The original `post_tool_use.py` did `str(tool_response)`,
  which serialized this whole dict — including full file diffs — into the
  buffer as noisy Python-repr text. Fixed: `_describe_tool_response()` now
  extracts only `type` + file path, falling back to `json.dumps` only for
  unrecognized dict shapes, so the buffer never carries full diff content.
  This was caught before merge, from real evidence, not by guesswork.
- Still unconfirmed live: whether `Stop`'s payload includes a distinct
  turn identifier (no real Stop event captured yet this session). The
  `turn_id` synthesis strategy (sequential counter) stands as designed.

`.claude/logs/` added to a new root `.gitignore` — it's runtime
session/buffer data, not source, and must not be committed.
