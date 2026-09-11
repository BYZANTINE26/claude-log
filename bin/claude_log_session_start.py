#!/usr/bin/env python3
"""Thin wrapper Claude Code invokes by absolute path for SessionStart.

Inserts the repo root onto sys.path so `claude_log` is importable without
depending on how Claude Code resolves cwd/PYTHONPATH for hook commands.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claude_log.hooks.session_start import run  # noqa: E402

if __name__ == "__main__":
    run()
