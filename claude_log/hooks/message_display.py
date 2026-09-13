#!/usr/bin/env python3
"""MessageDisplay hook: accumulate assistant message text into the
turn's buffer (see docs/adr/0005). Display-only event — no
systemMessage, no decision control, per the hooks reference.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from claude_log import config as config_module
from claude_log.buffer import append_message_delta
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

    append_message_delta(
        config_module.buffer_path(project_root, session_id, prompt_id),
        hook_input.get("message_id", ""),
        hook_input.get("delta", ""),
        hook_input.get("final", False),
    )
    emit_ok()


def run() -> None:
    """Guarded entry point: never let a bug block the user's session."""
    try:
        main()
    except Exception as error:  # noqa: BLE001 - never block the user's session
        config_module.get_logger().error("MessageDisplay hook failed: %s", error)
        emit_ok()


if __name__ == "__main__":
    run()
