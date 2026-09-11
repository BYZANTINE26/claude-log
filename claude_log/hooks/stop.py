"""Stop hook: read+clear the turn buffer, summarize once, append one entry.

This is the only hook that writes to the session log — the others only
accumulate into the per-turn buffer. Batching this way means exactly one
summarization call per turn, regardless of how many tool calls happened.
"""

import sys
from datetime import datetime, timezone

from claude_log import config as config_module
from claude_log import logger, metadata, summarizer
from claude_log.buffer import read_and_clear
from claude_log.hooks._hook_io import emit_ok, read_hook_input, resolve_project_root
from claude_log.paths import log_file_path, turn_buffer_path


def main() -> None:
    hook_input = read_hook_input()
    project_root = resolve_project_root(hook_input)
    config = config_module.load_config(project_root)

    if not config.get("enabled", True):
        emit_ok()
        return

    session_id = hook_input.get("session_id", "unknown-session")
    buffer_path = turn_buffer_path(project_root, session_id, config)
    buffered_turn = read_and_clear(buffer_path)

    if not buffered_turn["prompt"] and not buffered_turn["tool_calls"]:
        emit_ok()  # nothing happened this turn — nothing to log
        return

    log_path = log_file_path(project_root, session_id, config)
    logger.initialize_or_resume(project_root, session_id, config)

    tool_calls = buffered_turn["tool_calls"]
    refs = {
        "commit": metadata.current_commit_hash(project_root),
        "files": metadata.files_touched(tool_calls),
        "tools": [call.get("tool_name", "?") for call in tool_calls],
    }
    recent_entries = logger.get_recent_entries(
        log_path, config["recent_context_window"]
    )
    summary = summarizer.summarize(recent_entries, buffered_turn, config)

    turn_id = f"{session_id}:{logger.count_entries(log_path)}"
    timestamp = datetime.now(timezone.utc).isoformat()
    context = buffered_turn if config["verbosity"] == "rich" else None
    entry = logger.build_entry(
        turn_id, timestamp, summary, refs, context, config["verbosity"]
    )
    logger.append_entry(log_path, entry)
    emit_ok()


def run() -> None:
    """Guarded entry point: never let a bug block the user's session."""
    try:
        main()
    except Exception as error:  # noqa: BLE001 - never block the user's session
        print(f"claude-log Stop failed: {error}", file=sys.stderr)
        emit_ok()


if __name__ == "__main__":
    run()
