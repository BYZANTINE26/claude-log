---
Status: accepted
---

# Drop Rich verbosity and per-tool-call tracking; derive turn context from prompt + response + git diff

Rich mode and the `PostToolUse` hook existed to capture "what happened
in this turn" via each tool's input/output. In practice Claude's own
response text already narrates what it did (e.g. "added `add_numbers()`
for X"), making per-tool-call capture redundant for summarization
purposes and a recurring source of token bloat (raw `tool_input`/
`tool_response` content leaking into the log). Dropping it: only
`UserPromptSubmit` (captures the prompt) and `Stop` (captures
`last_assistant_message`) remain as hooks; there is only one log entry
shape (the former Slim shape), no Rich variant.

File-touch tracking moves from per-tool-call accumulation to a git-based
snapshot diff. `UserPromptSubmit` records `commit_before` plus a
`dirty_before` map of `{path: git hash-object <path>}` for every path in
`git status --porcelain` (covers both tracked-uncommitted and untracked
files, since `hash-object` works on either). `Stop` records `commit_after`
and recomputes the same map as `dirty_after`. Touched files are the union
of:
- `git diff --name-only commit_before..commit_after` (everything
  committed during the turn — insensitive to how many commits happened
  in between or whether a branch switch occurred, since it's a pure
  content diff between two hashes)
- every path in `dirty_after` whose hash differs from (or is absent from)
  `dirty_before` — i.e. newly dirtied or further-modified files,
  tracked or untracked

A plain `git status --porcelain` snapshot at `Stop` alone was rejected:
it would attribute any file left dirty *before* the turn started to this
turn, even if the turn never touched it. Hashing only the (typically
small) dirty set at each boundary is cheap and correctly handles both
directions: a pre-existing dirty file (tracked or untracked) left
untouched keeps the same hash and is excluded; a pre-existing dirty file
that the turn *does* further modify gets a new hash and is included, the
same as a brand-new untracked file. There is no separate "untracked"
case — `hash-object` and the `dirty_before`/`dirty_after` comparison
treat tracked-uncommitted and untracked paths identically.

## Considered Options
- Keep `PostToolUse` and track tool calls, but truncate/describe instead
  of storing raw payloads (the previous fix attempt) — rejected: still
  bloats the turn buffer and is redundant with what the assistant's own
  response already conveys.
- Store a single `commit` field, snapshotted once — rejected: ambiguous
  when a turn spans multiple commits or a branch switch; a before/after
  pair with an explicit diff is unambiguous and lets a deep-dive
  reconstruct exact intermediate history via `git log commit_before..commit_after`.

## Consequences
- `refs.files` in a log entry means "changed on disk during this turn,"
  not "explicitly edited by a tool call" — a file changed by, say, a
  build step or an external process during the turn would also show up.
- If `commit_before`/`commit_after` are later invalidated (amend, rebase,
  reset), the diff can no longer be reconstructed — same class of
  limitation as any commit-hash-based audit trail, accepted for MVP.
