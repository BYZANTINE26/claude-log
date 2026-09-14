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

_COMPILE_SYSTEM_PROMPT = (
    "You are claude-log's history compiler. Given a chronological list of "
    "past turn summaries, consolidate them into one coherent account of "
    "what happened across the whole session — a short narrative, not a "
    "restatement of each line. Return only the requested structured JSON "
    "output."
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
    user_content = _build_user_content(recent_entries, prompt, assistant_messages)
    return _call_endpoint(config.get("summarization_endpoint"), _SYSTEM_PROMPT, user_content, "summarize")


def compile_summaries(summaries: list[str], config: dict) -> str | None:
    """One consolidated narrative from several past turn summaries, or
    None if the call failed for any reason (BACKLOG.md #22) — same
    honest-failure contract as `summarize()`; the caller decides how to
    degrade (currently: fall back to printing the summaries as-is)."""
    user_content = _build_compile_content(summaries)
    return _call_endpoint(
        config.get("summarization_endpoint"), _COMPILE_SYSTEM_PROMPT, user_content, "compile_summaries"
    )


def _call_endpoint(endpoint_config: dict | None, system_prompt: str, user_content: str, log_context: str) -> str | None:
    """Shared dispatch/error-handling for both `summarize()` and
    `compile_summaries()` — same endpoint config, same two provider
    paths, same never-fabricate-on-failure contract, just a different
    prompt and payload per caller."""
    is_claude_code = bool(endpoint_config) and endpoint_config.get("provider") == "claude-code"
    if not endpoint_config or not (is_claude_code or endpoint_config.get("url")):
        get_logger().warning("%s: no summarization_endpoint configured", log_context)
        return None

    try:
        if is_claude_code:
            result = call_claude_code_provider(endpoint_config, system_prompt, user_content)
        else:
            result = call_openai_compatible_endpoint(endpoint_config, system_prompt, user_content)
    except Exception as error:  # noqa: BLE001 - any failure -> caller degrades, never fabricated
        get_logger().error("%s: endpoint call failed: %s", log_context, error)
        return None

    if not result or not result.strip():
        get_logger().warning("%s: endpoint returned an empty result", log_context)
        return None
    get_logger().debug("%s: got a %d-character result", log_context, len(result))
    return result


def call_openai_compatible_endpoint(endpoint_config: dict, system_prompt: str, user_content: str) -> str:
    """POST to `<url>` with an OpenAI-compatible `/v1/chat/completions`
    body; raises on any network, HTTP, or unexpected-shape error."""
    request_body = {
        "model": endpoint_config["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
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


def call_claude_code_provider(endpoint_config: dict, system_prompt: str, user_content: str) -> str:
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

    full_prompt = f"{system_prompt}\n\n{user_content}"
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


def _build_compile_content(summaries: list[str]) -> str:
    numbered_lines = [f"{index + 1}. {summary}" for index, summary in enumerate(summaries)]
    return "Turn summaries, in order:\n" + "\n".join(numbered_lines)
