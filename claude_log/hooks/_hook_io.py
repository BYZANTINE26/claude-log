"""Shared stdin/stdout helpers for Claude Code hook entry points.

Field names below (session_id, cwd, prompt, tool_name, tool_input,
tool_response) reflect claude-log's best understanding of the Claude Code
hook JSON contract, unverified against a live session — see
.planning/findings.md. Every accessor uses .get() with a safe default so a
wrong field name degrades a hook to a generic fallback instead of crashing
the user's session.
"""

# TODO: Go through the hooks documentation at -
#   https://code.claude.com/docs/en/hooks.md and understand the hooks schema
#   then if required modify this code accordingly.

import json
import os
import sys


def read_hook_input() -> dict:
    """Parse the JSON object Claude Code sends on stdin.

    An empty or malformed payload returns {} rather than raising, so a
    hook can still emit_ok() and never block the user's turn.
    """
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            return {}
        return json.loads(raw_input)
    except (json.JSONDecodeError, OSError):
        return {}


def emit_ok(extra: dict | None = None) -> None:
    """Print an empty/extra JSON object and exit 0.

    Claude Code hooks are expected to exit 0 for normal completion;
    claude-log never blocks or modifies the user's turn.
    """
    print(json.dumps(extra or {}))
    sys.exit(0)


def resolve_project_root(hook_input: dict) -> str:
    """Best-effort project root: hook's reported cwd, else the real cwd."""
    return hook_input.get("cwd") or os.getcwd()
