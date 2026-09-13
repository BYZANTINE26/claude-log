#!/usr/bin/env python3
"""SessionStart hook: mark a context-reset boundary on `/clear`.

On `source: "resume"` or plain `startup`, this does nothing — no reset
marker means get_recent_entries() falls back to the full configured
window, so a resumed session has full recent-log context immediately
(see docs/adr/0007 and SPEC.md's SessionStart bullet).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from claude_log import config as config_module
from claude_log import logger
from claude_log.hooks._hook_io import emit_ok, read_hook_input, resolve_project_root


def main() -> None:
    hook_input = read_hook_input()
    config = config_module.load_config()
    if not config["enabled"]:
        emit_ok()
        return

    if hook_input.get("source") == "clear":
        project_root = resolve_project_root(hook_input)
        session_id = hook_input.get("session_id", "unknown-session")
        logger.mark_context_reset(project_root, session_id)

    emit_ok()


def run() -> None:
    """Guarded entry point: never let a bug block the user's session."""
    try:
        main()
    except Exception as error:  # noqa: BLE001 - never block the user's session
        config_module.get_logger().error("SessionStart hook failed: %s", error)
        emit_ok()


if __name__ == "__main__":
    run()
