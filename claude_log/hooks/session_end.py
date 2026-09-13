#!/usr/bin/env python3
"""SessionEnd hook: final orphan-buffer sweep (see docs/adr/0007).

Fires on true termination, /exit, /clear, and /resume alike (confirmed
from the hooks reference's own SessionEnd section) — sweeps every
leftover buffer for this session unconditionally, since there's no
"current" turn to protect at session end.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from claude_log import config as config_module
from claude_log import logger
from claude_log.buffer import sweep_orphaned
from claude_log.hooks._hook_io import emit_ok, read_hook_input, resolve_project_root


def main() -> None:
    hook_input = read_hook_input()
    config = config_module.load_config()
    if not config["enabled"]:
        emit_ok()
        return

    project_root = resolve_project_root(hook_input)
    session_id = hook_input.get("session_id", "unknown-session")

    lost_markers = sweep_orphaned(project_root, session_id, keep_prompt_id="")
    if lost_markers:
        log_path = logger.initialize_or_resume(project_root, session_id)
        for marker in lost_markers:
            logger.append_entry(log_path, marker)
        config_module.get_logger().info(
            "SessionEnd: swept %d orphaned turn(s) for session %s", len(lost_markers), session_id
        )
    else:
        config_module.get_logger().debug("SessionEnd: no orphaned buffers for session %s", session_id)

    emit_ok()  # SessionEnd discards systemMessage per the hooks reference


def run() -> None:
    """Guarded entry point: never let a bug block the user's session."""
    try:
        main()
    except Exception as error:  # noqa: BLE001 - never block the user's session
        config_module.get_logger().error("SessionEnd hook failed: %s", error)
        emit_ok()


if __name__ == "__main__":
    run()
