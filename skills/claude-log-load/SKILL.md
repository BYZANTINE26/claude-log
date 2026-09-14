---
description: Manually re-ingest recent claude-log entries into a fresh (post-/clear) context window. Use when the user runs /claude-log-load.
disable-model-invocation: true
---

# claude-log-load

Run this exact command from the project root, using the count the user
gave after the skill name (default `10` if none given):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/claude_log/cli.py" "$ARGUMENTS"
```

If `$ARGUMENTS` is empty, omit it so the script's own default (10) applies.

The command prints the most recent claude-log entries for this project's
current session, led by a
`claude-log: recent session summaries (background context, no action
needed):` header, then a numbered list of summaries, one per line (no
metadata — `turn_id`/timestamp/git refs stay in the log file, they're
not re-ingested). Entries with no real summary — `summary_failed` or
`turn_lost` markers — are skipped entirely, so the printed list may be
shorter than the requested count. Read them to understand what happened
in this session before the current context window began, then hold onto
the recovered context and use it as necessary. Do not explain the
mechanics of this command to the user unless asked.
