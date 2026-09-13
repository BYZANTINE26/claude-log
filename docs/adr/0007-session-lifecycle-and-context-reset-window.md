---
Status: accepted
---

# Session lifecycle: clear-boundary reset, growing window, manual re-ingestion, and end-of-session sweep

A fresh context window (`/clear`) shouldn't silently inherit
summarization context from before the clear — but the docs don't confirm
whether `/clear` reuses the same `session_id` or starts a new one, so the
design must be correct either way (same pattern as ADR-0006).

`SessionStart` fires with `source: "clear"` (among `startup`/`resume`/
`compact`/`fork`, via its matcher). On that source, the hook writes a
small per-session state file,
`<project>/.claude-log/.state/<session_id>.json`, recording
`reset_at_entry_index` (the log's current entry count at the moment of
clear) and `reingested_count: null`. If `/clear` actually started a new
`session_id`, this state file and the reset entry index are simply never
consulted (the new session resolves to a different, empty log) — the
mechanism is a no-op in that case, not a wrong answer.

`get_recent_entries` then computes the context window size as
`min(configured_N, reingested_count_or_0 + entries_since_reset)`, where
`entries_since_reset` is just the log's current entry count minus
`reset_at_entry_index`. No separate "current window size" counter is
needed: this naturally grows by one every turn as new entries are
appended post-clear, and naturally starts from whatever `reingested_count`
was set to. If no reset has ever happened, `reset_at_entry_index` is
absent and the full configured window applies as before (covers
`resume` and plain `startup`).

**Manual re-ingestion** is a plugin-shipped skill, `/claude-log-load
[count]` (default 10), not a hook — skills are genuinely user-invocable
slash commands (unlike hooks, which cannot be triggered by typed input).
Invoking it tells Claude to read the last `count` entries from the
current session's log file directly (via a small bundled script that
resolves the correct log path, so Claude doesn't have to guess it) and
sets `reingested_count = count` in the state file.

**`SessionEnd`** performs a final orphan sweep: any buffer file still
present for the ending `session_id` (per ADR-0006's `turn_lost` marker
mechanism) is marked and cleaned up within `SessionEnd`'s ~1.5-second
budget, covering the case where a session terminates (crash, `/exit`)
after an interrupted final turn with no subsequent `UserPromptSubmit` to
trigger the usual sweep. `SessionEnd` also fires with `reason: "clear"`
or `"resume"` (not just true termination) — confirmed from the hooks
reference's dedicated `SessionEnd` section, correcting an earlier
summary-table pass that mis-stated the field as `end_reason` instead of
`reason`. The orphan sweep runs unconditionally on every `SessionEnd`
regardless of `reason`, so this doesn't change the design, only confirms
it also catches a turn interrupted right before a `/clear`.

## Considered Options
- An explicit incrementing "window size" counter, bumped by +1 each turn
  post-clear — rejected: redundant, since `entries_since_reset` is
  already a free-standing derived value (current count minus the stored
  reset index); tracking it separately is a second source of truth that
  could drift.
- Implement `/claude-log-load` by having a `UserPromptSubmit` hook parse
  the literal prompt text for a magic command — rejected: skills are the
  actual mechanism Claude Code provides for user-typed commands; hooks
  fire on lifecycle events, not on command dispatch.

## Consequences
Every session gets a small `.claude-log/.state/<session_id>.json` file
in addition to its log and any transient buffers — a third piece of
per-session state to account for when reasoning about what's on disk.
