# claude-log

A lightweight, token-efficient session logging system for Claude Code that
maintains an append-only log of session turns with concise summaries and
metadata for seamless session resumption and deep-dive investigation.

## Problem It Solves

Existing session tracking tools (claude-mem, session summarizers) waste tokens
by:
- Sending full conversation history at every turn
- Creating verbose, redundant summaries
- Losing the chronological journey of how work unfolded

With large contexts (500K+ tokens), this token waste makes them impractical.

## How It Works

**claude-log** uses a log-based approach inspired by distributed systems (RAFT
logs, event sourcing):

1. **Automatic hook** captures each Claude Code turn
2. **Local summarization endpoint** generates a crisp 1-2 line summary using
   only recent log context (not full history)
3. **Append-only log** stores the summary + metadata (commit hash, files
   touched, Claude turn ID)
4. **Seamless resume** — when a session resumes, append to the existing log,
   not create a new one

Result: **<20% of claude-mem's token cost** for equivalent context preservation,
with full chronological journey and deep-dive capabilities.

## Architecture

```
📦 claude-log/
├── INTENT.md               ← Problem, desired outcome, success criteria
├── SPEC.md                 ← System requirements and architecture
├── README.md               ← This file
├── CHANGELOG.md            ← Release history
├── BACKLOG.md              ← Deferred items
├── claude_log/             ← Core Python package (config, buffer, logger,
│                              summarizer, metadata, hooks/)
├── bin/                    ← Hook wrapper scripts Claude Code invokes
├── tests/                  ← 37 tests covering the package above
├── docs/
│   └── specs/
│       └── core-logging.md ← Component-level design
└── .claude/
    ├── CLAUDE.md           ← Project conventions
    ├── settings.json       ← Claude Code configuration + hook registration
    ├── claude_log_config.json  ← claude-log's own runtime config
    ├── logs/               ← Session logs (created at runtime, gitignored)
    ├── plans/              ← Planning artifacts
    └── scratchpad/         ← Temporary experiments and scripts
```

## Development Status

🚧 **Core Logging MVP built** — see `CHANGELOG.md` for what's landed.

- [x] Brainstorming & direction clarity
- [x] Intent & specification
- [x] Implementation plan (`.claude/plans/PLAN.md`)
- [x] Core logging module (`claude_log/`, 37 tests passing)
- [ ] Real summarization endpoint integration (currently rule-based only)
- [ ] Benchmarking suite (vs. claude-mem)
- [ ] Documentation & examples

## Getting Started

1. Review `INTENT.md` for the problem and goals
2. Review `SPEC.md` for system architecture
3. Review `docs/specs/core-logging.md` for component design
4. Run the test suite: `python3 -m pytest tests/ -v`
5. Hooks are already registered in `.claude/settings.json` — sessions in
   this project log automatically to `.claude/logs/`

## Key Features (MVP)

- ✅ Project-scoped, session-specific logs
- ✅ Resume-aware (append to existing log on session resume)
- ✅ Automatic hook-based logging (no manual intervention)
- ✅ Configurable verbosity (slim vs. rich entries)
- ✅ Metadata preservation (turn ID, commit, files, tools)
- ✅ Chronological journey (walk the log to see how you got here)

## Benchmarking

A key success criterion is proving token efficiency vs. existing tools:
- **claude-mem**: Full history at every turn (high token waste)
- **Session summarizers**: Bloated summaries
- **claude-log**: Recent context + current turn only (target: <20% of
  claude-mem cost)

Benchmarking suite to be built as part of MVP.

## License

TBD

## Contributing

See `CLAUDE.md` for project conventions and workflow.
