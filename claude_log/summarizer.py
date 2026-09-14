"""Turn summarization, either via an OpenAI-compatible chat-completions
endpoint or, as an alternative, through the user's own Claude Code login
(`"provider": "claude-code"` in `summarization_endpoint`, BACKLOG.md #20).

No rule-based fallback: per docs/adr/0003, a failure (endpoint
unreachable, timeout, malformed response) must never produce a
fabricated summary — `summarize()` returns None and the caller (Stop
hook) writes a `summary_failed` marker entry instead.
"""

import json
import os
import subprocess
import urllib.request

from claude_log.config import get_logger

_SYSTEM_PROMPT = (
    "You are claude-log's turn summarizer. Given recent turn summaries "
    "for context and the current turn's user message and assistant "
    "messages, write a 1-2 line summary of what this turn accomplished. "
    "Return only the requested structured JSON output."
)

_RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "summary_response",
        "schema": {
            "type": "object",
            "properties": {"summary": {"type": "string"}},
            "required": ["summary"],
            "additionalProperties": False,
        },
        "strict": True,
    },
}


def summarize(
    recent_entries: list[dict], prompt: str, assistant_messages: list[str], config: dict
) -> str | None:
    """A 1-2 line summary, or None if summarization failed for any reason."""
    endpoint_config = config.get("summarization_endpoint")
    is_claude_code = bool(endpoint_config) and endpoint_config.get("provider") == "claude-code"
    if not endpoint_config or not (is_claude_code or endpoint_config.get("url")):
        get_logger().warning("summarize: no summarization_endpoint configured")
        return None

    try:
        if is_claude_code:
            summary = call_claude_code_provider(
                endpoint_config, recent_entries, prompt, assistant_messages
            )
        else:
            summary = call_openai_compatible_endpoint(
                endpoint_config, recent_entries, prompt, assistant_messages
            )
    except Exception as error:  # noqa: BLE001 - any failure -> summary_failed, never fabricated
        get_logger().error("summarize: endpoint call failed: %s", error)
        return None

    if not summary or not summary.strip():
        get_logger().warning("summarize: endpoint returned an empty summary")
        return None
    get_logger().debug("summarize: got a %d-character summary", len(summary))
    return summary


def call_openai_compatible_endpoint(
    endpoint_config: dict, recent_entries: list[dict], prompt: str, assistant_messages: list[str]
) -> str:
    """POST to `<url>` with an OpenAI-compatible `/v1/chat/completions`
    body; raises on any network, HTTP, or unexpected-shape error."""
    request_body = {
        "model": endpoint_config["model"],
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_content(recent_entries, prompt, assistant_messages)},
        ],
        "stream": False,
        "response_format": _RESPONSE_SCHEMA,
        **endpoint_config.get("extra_params", {}),
    }

    headers = {"Content-Type": "application/json"}
    if endpoint_config.get("api_key"):
        headers["Authorization"] = f"Bearer {endpoint_config['api_key']}"

    request = urllib.request.Request(
        endpoint_config["url"],
        data=json.dumps(request_body).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=endpoint_config.get("timeout_seconds", 30)) as response:
        response_body = json.loads(response.read())

    content = response_body["choices"][0]["message"]["content"]
    return json.loads(content)["summary"]


def call_claude_code_provider(
    endpoint_config: dict, recent_entries: list[dict], prompt: str, assistant_messages: list[str]
) -> str:
    """Summarize via a `claude -p` subprocess, authenticated through
    whatever login the running Claude Code CLI already has — no separate
    API key (BACKLOG.md #20). Raises on any subprocess, timeout, or
    unexpected-output error, same contract as the HTTP path.

    `--safe-mode` disables hooks/plugins/MCP for this subprocess, so it
    can't re-trigger claude-log's own hooks — confirmed live, not just
    assumed (see `.planning/findings.md`). `--tools ""` also disables
    built-in tools: this call must only generate text, never act.
    `MAX_THINKING_TOKENS=0` disables extended thinking (has no effect on
    Fable models, which can't disable thinking at all — surfaced as a
    warning rather than silently ignored).
    """
    model = endpoint_config["model"]
    if "fable" in model.lower():
        get_logger().warning(
            "summarize: MAX_THINKING_TOKENS=0 has no effect on Fable models (%s)", model
        )

    full_prompt = f"{_SYSTEM_PROMPT}\n\n{_build_user_content(recent_entries, prompt, assistant_messages)}"
    schema = json.dumps(_RESPONSE_SCHEMA["json_schema"]["schema"])

    environment = dict(os.environ)
    environment["MAX_THINKING_TOKENS"] = "0"

    result = subprocess.run(
        [
            "claude",
            "-p", full_prompt,
            "--model", model,
            "--output-format", "json",
            "--json-schema", schema,
            "--safe-mode",
            "--tools", "",
        ],
        capture_output=True,
        text=True,
        timeout=endpoint_config.get("timeout_seconds", 60),
        env=environment,
        check=True,
    )
    response = json.loads(result.stdout)
    return response["structured_output"]["summary"]


def _build_user_content(recent_entries: list[dict], prompt: str, assistant_messages: list[str]) -> str:
    recent_lines = [
        f"{index + 1}. {entry.get('summary', '[no summary]')}"
        for index, entry in enumerate(recent_entries)
    ]
    recent_block = "\n".join(recent_lines) if recent_lines else "(none)"

    turn_lines = [f"User: {prompt}"] + [f"Assistant: {message}" for message in assistant_messages]
    turn_block = "\n".join(turn_lines)

    return f"Recent turns:\n{recent_block}\n\nCurrent turn:\n{turn_block}"
