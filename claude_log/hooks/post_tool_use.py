"""PostToolUse hook: record one tool call into the turn buffer.

Only a short description of the tool's result is kept, never the full raw
output — tool_response for Edit/Write arrives as a dict containing the
entire old/new file content, and dumping that (even truncated) would
reintroduce the exact token bloat this project exists to avoid.
"""

import json
import sys

from claude_log import config as config_module
from claude_log.buffer import append_tool_call
from claude_log.hooks._hook_io import emit_ok, read_hook_input, resolve_project_root
from claude_log.paths import turn_buffer_path

_MAX_RESULT_SUMMARY_LENGTH = 200


def main() -> None:
    hook_input = read_hook_input()
    project_root = resolve_project_root(hook_input)
    config = config_module.load_config(project_root)

    if not config.get("enabled", True):
        emit_ok()
        return

    session_id = hook_input.get("session_id", "unknown-session")
    tool_name = hook_input.get("tool_name", "unknown_tool")
    tool_input = hook_input.get("tool_input", {})
    result_summary = _describe_tool_response(hook_input.get("tool_response"))

    append_tool_call(
        turn_buffer_path(project_root, session_id, config),
        tool_name,
        result_summary,
        tool_input,
    )
    emit_ok()


def _describe_tool_response(tool_response) -> str:
    """A short descriptor, never the full content of a dict-shaped response.

    Edit/Write tool responses carry the entire old/new file content —
    surfacing a couple of identifying fields (type, file path) is enough
    for the rule-based summarizer; the full diff has no place in a log
    entry meant to stay 1-2 lines.
    """
    if isinstance(tool_response, dict):
        response_type = tool_response.get("type")
        file_path = tool_response.get("filePath") or tool_response.get("file_path")
        descriptor = " ".join(str(part) for part in (response_type, file_path) if part)
        return _truncate(descriptor or json.dumps(tool_response, default=str))
    return _truncate(str(tool_response) if tool_response is not None else "")


def _truncate(text: str) -> str:
    if len(text) <= _MAX_RESULT_SUMMARY_LENGTH:
        return text
    return text[: _MAX_RESULT_SUMMARY_LENGTH - 1] + "…"


def run() -> None:
    """Guarded entry point: never let a bug block the user's session."""
    try:
        main()
    except Exception as error:  # noqa: BLE001 - never block the user's session
        print(f"claude-log PostToolUse failed: {error}", file=sys.stderr)
        emit_ok()


if __name__ == "__main__":
    run()
