---
Status: accepted
---

# Capture every assistant message in a turn, not just the final one

`Stop`'s `last_assistant_message` field only carries the final message
of a turn, but Claude can emit multiple text messages within one turn
(e.g. commentary before a tool call, then a closing summary). Relying on
only the last one loses earlier context that the final message doesn't
restate. `MessageDisplay` fires once per displayed assistant message
during the turn; the hook appends each one's text to the turn's buffer,
and `Stop` summarizes the full accumulated sequence instead of a single
message.

## Considered Options
- Use only `last_assistant_message` (previous design) — simplest, but
  silently drops earlier messages whose content never resurfaces in the
  final one.

## Consequences
Adds a third hook (`MessageDisplay`) alongside `UserPromptSubmit` and
`Stop`. The buffer still only ever holds message *text*, never tool
payloads — consistent with ADR-0004's "what was said, not what was
operated on" boundary.
