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
current session, one JSON object per line — each is a prior turn's
summary and metadata. Read them to understand what happened in this
session before the current context window began, then continue the
conversation with that understanding. Do not explain the mechanics of
this command to the user unless asked; just use the recovered context.
