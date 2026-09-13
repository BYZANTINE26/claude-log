---
Status: accepted
---

# Key turn buffers by `prompt_id`, not `session_id`

The previous design keyed the turn buffer file by `session_id` alone,
assuming exactly one turn is ever in flight per session. That breaks
under interruption (Ctrl+C mid-generation) or a prompt queued before the
prior turn's `Stop` fires: a second `UserPromptSubmit` could start
writing into the same buffer file the first turn hasn't been read out
of yet, corrupting both turns' data. Since `prompt_id` (a UUID, per
ADR — see turn-identity decision) is unique per turn and present on
every hook event, the buffer path becomes
`<project>/.claude-log/.buffers/<session_id>__<prompt_id>.json` — each
turn gets its own file (flat directory, `session_id` kept in the
filename so a session's leftover buffers can still be found by prefix),
so overlapping or interrupted turns can never collide.

On every `UserPromptSubmit`, before creating the new turn's buffer, the
hook lists the buffer directory for files prefixed `<session_id>__`: any
one other than the file about to be created is a leftover from a turn
that never reached
`Stop` (crash, interrupt, or an as-yet-unconfirmed queueing edge case —
see the `research` ticket in `BACKLOG.md`). Each leftover is logged as a
`"turn_lost": true` marker entry (per ADR-0003) and deleted, rather than
guessed at or silently merged into the new turn.

## Considered Options
- Keep `session_id`-only keying and rely on Claude Code never actually
  overlapping turns — rejected: the exact interrupt/queueing behavior is
  undocumented (confirmed via the hooks reference), so building on an
  unverified assumption risks silently corrupting two turns' data instead
  of failing safely.

## Consequences
Orphan detection now runs on every `UserPromptSubmit`, not just
`SessionStart` — a small, constant-cost directory listing. Whether the
underlying cause was a crash, an interrupt, or overlap, the outcome is
identical and safe: an honest `turn_lost` marker, never fabricated or
merged content.
