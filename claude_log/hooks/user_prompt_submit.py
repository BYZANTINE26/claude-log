#!/usr/bin/env python3
"""UserPromptSubmit hook: start a new turn's buffer.

Also sweeps any buffer left over from a turn that never reached Stop
(crash, or confirmed: an interrupted turn never fires Stop at all — see
docs/adr/0006) before starting the new one, so a lost turn is recorded
as an honest marker rather than silently bleeding into this turn.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from claude_log import config as config_module
from claude_log import git_snapshot, logger
from claude_log.buffer import sweep_orphaned, start_turn
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

    lost_markers = sweep_orphaned(project_root, session_id, prompt_id)
    if lost_markers:
        log_path = logger.initialize_or_resume(project_root, session_id)
        for marker in lost_markers:
            logger.append_entry(log_path, marker)
        config_module.get_logger().info(
            "UserPromptSubmit: swept %d orphaned turn(s) for session %s",
            len(lost_markers), session_id,
        )

    snapshot = git_snapshot.snapshot_git_state(project_root)
    start_turn(
        config_module.buffer_path(project_root, session_id, prompt_id),
        hook_input.get("prompt", ""),
        snapshot["commit"],
        snapshot["dirty"],
    )
    config_module.get_logger().debug("UserPromptSubmit: started buffer for turn %s", prompt_id)

    system_message = (
        f"claude-log: recorded {len(lost_markers)} lost turn(s) from an "
        "interruption or crash" if lost_markers else None
    )
    emit_ok(system_message)


def run() -> None:
    """Guarded entry point: never let a bug block the user's session."""
    try:
        main()
    except Exception as error:  # noqa: BLE001 - never block the user's session
        config_module.get_logger().error("UserPromptSubmit hook failed: %s", error)
        emit_ok()


if __name__ == "__main__":
    run()
