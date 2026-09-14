"""Shared stdin/stdout contract for every claude-log hook.

Field names below are confirmed directly from Claude Code's hooks
reference per-event sections (not just its summary table — two earlier
summary-table passes had real errors: SessionEnd's field is `reason`
not `end_reason`, and UserPromptSubmit's is `prompt` not `user_prompt`).
"""

import json
import sys


def read_hook_input() -> dict:
    return json.load(sys.stdin)


def emit_ok(system_message: str | None = None) -> None:
    """Exit 0, optionally surfacing `system_message` to the user.

    `systemMessage` is a universal JSON output field (see hooks
    reference, JSON output table) — this is how a summarize failure or
    an orphaned turn (docs/adr/0003, docs/adr/0006) gets noticed, since
    the log itself only ever gets an honest marker, never fabricated text.
    """
    if system_message:
        print(json.dumps({"systemMessage": system_message}))
    sys.exit(0)


def resolve_project_root(hook_input: dict) -> str:
    return hook_input.get("cwd") or "."
