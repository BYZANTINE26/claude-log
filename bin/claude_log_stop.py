#!/usr/bin/env python3
"""Thin wrapper Claude Code invokes by absolute path for Stop."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claude_log.hooks.stop import run  # noqa: E402

if __name__ == "__main__":
    run()
