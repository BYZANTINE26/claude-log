#!/usr/bin/env python3
"""`/claude-log-load [count]` skill support (see docs/adr/0007).

Run from the project directory the skill invokes it in. Prints the last
`count` log entries (for Claude to read as conversation context) and
records `count` as this session's reingested_count, so the context-reset
window formula in logger.py grows from that point forward.

Finding "the current session": skills have no direct session_id the way
hooks do, so this picks the most-recently-modified session log under
`.claude-log/logs/` — correct for the common single-active-session case;
ambiguous with two concurrent sessions on the same project, the same
known limitation as the no-file-locking backlog item.
"""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claude_log.config import project_log_dir
from claude_log.logger import record_reingestion


def load_recent(project_root: str, count: int) -> list[dict]:
    """Print the last `count` entries and record the re-ingestion."""
    session_id = _most_recent_session_id(project_root)
    if session_id is None:
        print("claude-log: no session log found for this project.")
        return []

    log_path = os.path.join(project_log_dir(project_root), "logs", f"{session_id}.jsonl")
    with open(log_path, "r", encoding="utf-8") as log_file:
        entries = [json.loads(line) for line in log_file if line.strip()]

    recent = entries[-count:]
    for entry in recent:
        print(json.dumps(entry))

    record_reingestion(project_root, session_id, count)
    return recent


def _most_recent_session_id(project_root: str) -> str | None:
    logs_dir = os.path.join(project_log_dir(project_root), "logs")
    log_files = glob.glob(os.path.join(logs_dir, "*.jsonl"))
    if not log_files:
        return None
    newest = max(log_files, key=os.path.getmtime)
    return os.path.splitext(os.path.basename(newest))[0]


if __name__ == "__main__":
    load_recent(os.getcwd(), int(sys.argv[1]) if len(sys.argv) > 1 else 10)
