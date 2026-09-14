#!/usr/bin/env python3
"""`/claude-log-load [count] [--compiled]` skill support (see docs/adr/0007,
BACKLOG.md #22).

Run from the project directory the skill invokes it in. Prints the last
`count` entries' summaries only — never `turn_id`/`timestamp`/`refs`,
which exist for a human auditing the log file directly, not for
re-ingestion into the model's context window, and never a
`summary_failed`/`turn_lost` marker's placeholder text, since there's no
real summary to re-ingest from one. `count` itself still counts raw log
entries (matching the window-growth formula in logger.py, which does the
same), so fewer than `count` lines may actually print if any of the
tail entries are markers.

`--compiled` sends those summaries to the configured summarization
endpoint to be consolidated into one narrative instead of printed
line-by-line. If that call fails or no endpoint is configured, this
falls back to the normal line-by-line output — a degraded-but-present
result over an empty one, same philosophy as `summary_failed` markers.

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

from claude_log import config as config_module
from claude_log import summarizer
from claude_log.config import project_log_dir
from claude_log.logger import record_reingestion

_HEADER = "claude-log: recent session summaries (background context, no action needed):"


def load_recent(project_root: str, count: int, compiled: bool = False) -> list[dict]:
    """Print the last `count` entries' summaries (or, with `compiled`,
    one consolidated narrative from them) and record the re-ingestion.

    `summary_failed`/`turn_lost` entries have no real summary text, so
    they're skipped entirely rather than printed as a placeholder line
    — there's nothing useful to re-ingest from a marker, and the
    numbering only counts entries actually printed.

    The printed output is self-labeling (a leading "background context,
    no action needed" line, only when there's something to show) — the
    skill's own instructions already tell Claude how to treat this, but
    that framing lives upstream of the tool result, not attached to it,
    so this is defense in depth if the two ever get separated."""
    session_id = _most_recent_session_id(project_root)
    if session_id is None:
        print("claude-log: no session log found for this project.")
        return []

    log_path = os.path.join(project_log_dir(project_root), "logs", f"{session_id}.jsonl")
    with open(log_path, "r", encoding="utf-8") as log_file:
        entries = [json.loads(line) for line in log_file if line.strip()]

    recent = entries[-count:]
    summarized = [entry for entry in recent if "summary" in entry]
    if summarized:
        summaries = [entry["summary"] for entry in summarized]
        compiled_text = None
        if compiled:
            compiled_text = summarizer.compile_summaries(summaries, config_module.load_config())
        print(_HEADER)
        if compiled_text:
            print(compiled_text)
        else:
            for index, summary in enumerate(summaries):
                print(f"{index + 1}. {summary}")

    record_reingestion(project_root, session_id, count)
    return recent


def _most_recent_session_id(project_root: str) -> str | None:
    logs_dir = os.path.join(project_log_dir(project_root), "logs")
    log_files = glob.glob(os.path.join(logs_dir, "*.jsonl"))
    if not log_files:
        return None
    newest = max(log_files, key=os.path.getmtime)
    return os.path.splitext(os.path.basename(newest))[0]


def _parse_arguments(raw: str) -> tuple[int, bool]:
    """`raw` is everything after the skill name as one shell word (see
    skills/claude-log-load/SKILL.md — `"$ARGUMENTS"` is quoted, so
    "10 --compiled" arrives here as a single string, not pre-split
    argv entries). Order-independent; count defaults to 10."""
    count = 10
    compiled = False
    for token in raw.split():
        if token == "--compiled":
            compiled = True
        else:
            count = int(token)
    return count, compiled


if __name__ == "__main__":
    arg_count, arg_compiled = _parse_arguments(sys.argv[1]) if len(sys.argv) > 1 else (10, False)
    load_recent(os.getcwd(), arg_count, arg_compiled)
