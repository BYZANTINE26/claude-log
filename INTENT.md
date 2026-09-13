# claude-log: Intent

## Problem
Existing session tracking tools (claude-mem, summarizers, Claude Code's compact cmd)
waste tokens by sending full conversation history at every turn, creating verbose
summaries, and losing the chronological journey. Token waste is severe with large
contexts (500K+ tokens), making these tools impractical for real projects.

## Desired Outcome
A lightweight, append-only logging system that:
- Records **1-2 line summaries** of each turn/tool call using a local endpoint
- Keeps **only recent log context** (not full history) to generate summaries
- Preserves **chronological journey** — shows how you got to current state
- Supports **deep-dive reconstruction** via stored metadata (commit hashes, file
  paths, Claude turn IDs)
- Resumes seamlessly when a session is resumed (append to existing log, don't
  create new one)

## Key Insight
Like distributed data processing systems (RAFT logs, event sourcing), instead of
replicating state at each step, store only the steps. State can be reconstructed
cheaply without redundancy.

## Affected Users/Systems
- **Claude Code users** with long-running sessions, large projects, or limited
  token budgets
- **Teams resuming sessions** across multiple people
- **Session auditing & deep-dive investigation** use cases

## Constraints
- **Project-scoped logs** (one log per project, one per session, resumable)
- **Single entry shape** — a summary plus metadata; no bloated "rich" mode
  that re-embeds raw content (see `docs/adr/0004-*`)
- **Local-network summarization** via an OpenAI-compatible chat-completions
  endpoint (no cloud API calls, to preserve token efficiency)
- **Append-only** (logs are write-once, chronological)
- **Installable anywhere** — ships as a personal Claude Code plugin, not
  per-project hook configuration (see `docs/adr/0001-*`)

## Success Criteria
1. **Reduced token usage** — benchmark shows <20% of claude-mem's token cost
2. **Context richness** — log entries + metadata allow accurate session resumption
3. **Easy resumption** — new session can read log and pick up where previous left
4. **Benchmarked comparison** — prove superiority over existing tools in token
   usage, context fidelity, and resumability
5. **Log integrity** — a failure or interruption is always visible as an
   explicit marker, never a fabricated summary or a silent gap (see
   `docs/adr/0003-*`)

## Unresolved Questions (for refinement)
- Exact local model to run behind the OpenAI-compatible endpoint (left to
  the user's own setup; the contract is fixed, see `curl.sh` reference)
- Viewing/querying UI (MVP: just append-only file)
- Log retention & cleanup policy
- Whether `/clear` reuses `session_id` or starts a new one — undocumented;
  design is correct either way (see `docs/adr/0007-*`)
- Whether `Stop` fires on a Ctrl+C interrupt, and how a queued prompt
  sequences against the prior turn — undocumented; see the `research`
  ticket in `BACKLOG.md`
