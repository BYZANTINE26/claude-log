#!/usr/bin/env python3
"""Stop hook: the only hook that writes to the session log.

Reads+clears the turn's buffer, snapshots git state again to compute
touched files, summarizes, and appends exactly one entry — a real
summary, or a `summary_failed` marker if the endpoint call failed (never
a fabricated fallback, see docs/adr/0003).
"""

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from claude_log import config as config_module
from claude_log import git_snapshot, logger, summarizer
from claude_log.buffer import read_and_clear
from claude_log.hooks._hook_io import emit_ok, read_hook_input, resolve_project_root


def main() -> None:
    hook_input = read_hook_input()
    config = config_module.load_config()
    if not config["enabled"]:
        emit_ok()
        return

    project_root = resolve_project_root(hook_input)
    session_id = hook_input.get("session_id", "unknown-session")
    prompt_id = hook_input.get("prompt_id", "unknown-prompt")

    buffer_path = config_module.buffer_path(project_root, session_id, prompt_id)
    buffered_turn = read_and_clear(buffer_path)
    if not buffered_turn["prompt"] and not buffered_turn["assistant_messages"]:
        emit_ok()  # nothing happened this turn — nothing to log
        return

    before_snapshot = {
        "commit": buffered_turn["commit_before"],
        "dirty": buffered_turn["dirty_before"],
    }
    after_snapshot = git_snapshot.snapshot_git_state(project_root)
    refs = {
        "commit_before": before_snapshot["commit"],
        "commit_after": after_snapshot["commit"],
        "files": git_snapshot.files_touched(before_snapshot, after_snapshot, project_root),
    }

    log_path = logger.initialize_or_resume(project_root, session_id)
    recent_entries = logger.get_recent_entries(
        project_root, session_id, config["recent_context_window"]
    )
    summary = summarizer.summarize(
        recent_entries, buffered_turn["prompt"], buffered_turn["assistant_messages"], config
    )

    timestamp = datetime.now(timezone.utc).isoformat()
    system_message = None
    if summary is None:
        entry = logger.build_entry(prompt_id, timestamp, None, refs, failure_flag="summary_failed")
        system_message = "claude-log: summarization failed for this turn"
    else:
        entry = logger.build_entry(prompt_id, timestamp, summary, refs)

    logger.append_entry(log_path, entry)
    config_module.get_logger().info(
        "Stop: logged turn %s (summary_failed=%s, %d file(s) touched)",
        prompt_id, summary is None, len(refs["files"]),
    )
    emit_ok(system_message)


def run() -> None:
    """Guarded entry point: never let a bug block the user's session."""
    try:
        main()
    except Exception as error:  # noqa: BLE001 - never block the user's session
        config_module.get_logger().error("Stop hook failed: %s", error)
        emit_ok()


if __name__ == "__main__":
    run()
