"""Turn summarization: pluggable HTTP endpoint with a rule-based fallback.

MVP config leaves summarization_endpoint unset, so summarize() always
takes the rule-based path. The HTTP path is real and tested so a later
swap to a local model (e.g. Ollama) is a config change only, never a code
change here or in logger.py.
"""

import json
import sys
import urllib.error
import urllib.request

_NO_ENDPOINT_VALUES = (None, "", "local")


def summarize(recent_entries: list, current_turn: dict, config: dict) -> str:
    """Return a 1-2 line summary, falling back to the rule-based heuristic
    if no endpoint is configured or the endpoint call fails."""
    endpoint_url = config.get("summarization_endpoint")
    if endpoint_url in _NO_ENDPOINT_VALUES:
        return rule_based_summary(current_turn)

    try:
        return call_http_endpoint(endpoint_url, recent_entries, current_turn)
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as error:
        print(f"claude-log: summarization endpoint failed: {error}", file=sys.stderr)
        return rule_based_summary(current_turn)


def call_http_endpoint(
    endpoint_url: str,
    recent_entries: list,
    current_turn: dict,
    timeout_seconds: float = 5.0,
) -> str:
    """POST {"recent_entries", "current_turn"}, return the "summary" field."""
    payload = json.dumps(
        {"recent_entries": recent_entries, "current_turn": current_turn}
    ).encode("utf-8")
    request = urllib.request.Request(
        endpoint_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body["summary"]


def rule_based_summary(current_turn: dict) -> str:
    """Derive a 1-2 line summary from the accumulated turn buffer."""
    tool_calls = current_turn.get("tool_calls", [])
    prompt = current_turn.get("prompt")

    edit_tool_names = {"Edit", "Write", "NotebookEdit"}
    edit_calls = [
        call for call in tool_calls if call.get("tool_name") in edit_tool_names
    ]
    if edit_calls:
        first_edit = edit_calls[0]
        file_path = first_edit.get("tool_input", {}).get("file_path", "a file")
        summary = f"Edited {file_path}: {first_edit.get('result_summary', '')}"
    elif tool_calls:
        tool_names = ", ".join(call.get("tool_name", "?") for call in tool_calls)
        summary = f"Ran {len(tool_calls)} tool call(s): {tool_names}"
    elif prompt:
        summary = f"Responded to: {prompt[:80]}"
    else:
        summary = "Turn completed with no recorded activity."

    return _clip(summary)


def _clip(summary: str, max_length: int = 200) -> str:
    if len(summary) <= max_length:
        return summary
    return summary[: max_length - 1] + "…"
