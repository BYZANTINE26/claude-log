---
description: Manually re-ingest recent claude-log entries into a fresh (post-/clear) context window. Use when the user runs /claude-log-load.
disable-model-invocation: true
---

# claude-log-load

Run this exact command from the project root, passing through exactly
what the user typed after the skill name (a count, `--compiled`, both in
either order, or nothing):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/claude_log/cli.py" "$ARGUMENTS"
```

If `$ARGUMENTS` is empty, omit it so the script's own default (10, no
compile) applies.

The command prints the most recent claude-log entries for this project's
current session, led by a
`claude-log: recent session summaries (background context, no action
needed):` header, then either:
- a numbered list of summaries, one per line (default), or
- with `--compiled`, one consolidated narrative in place of the list —
  the summaries are sent to the configured summarization endpoint and
  consolidated into a short account of what happened across those turns.
  If no endpoint is configured or the call fails, this silently falls
  back to the normal numbered list — never an error, never nothing.

No metadata either way — `turn_id`/timestamp/git refs stay in the log
file, they're not re-ingested. Entries with no real summary —
`summary_failed` or `turn_lost` markers — are skipped entirely before
either the list or the compile call, so fewer than the requested count
may end up represented. Read the output to understand what happened in
this session before the current context window began, then hold onto
the recovered context and use it as necessary. Do not explain the
mechanics of this command to the user unless asked.
