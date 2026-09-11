# claude-log: Specification

## Overview
A lightweight, token-efficient session logging system for Claude Code that
maintains an append-only log of session turns with 1-2 line summaries and
metadata for seamless session resumption and deep-dive investigation.

## Architecture

### Components
1. **Core Logging** — Hook-based session logging, log file management,
   resumability
2. **Summarization** — Local endpoint integration for turn summarization
   (pluggable)
3. **Benchmarking** — Comparative analysis against existing tools (token usage,
   context fidelity, resumability)

### Data Flow
```
Claude Turn → Hook → Extract context → Summarization Endpoint → 
Generate 1-2 line summary → Append to log → Persist metadata → Complete turn
```

## Overall Requirements

### Functional
- **Project-scoped logging**: One log per project, one per session
- **Resume-aware**: Append to existing session log on resume, not create new
- **Automatic logging**: Hook-based trigger after each turn (no manual
  intervention)
- **Configurable verbosity**: Slim (summary + metadata only) or Rich (summary +
  full turn context)
- **Metadata preservation**: Store Claude turn ID, commit hash, file paths,
  timestamps
- **Chronological narrative**: Walk the log to see how a session unfolded

### Non-Functional
- **Token efficiency**: <20% of claude-mem's token cost for equivalent context
  preservation
- **Performance**: Minimal latency on turn completion (summarization endpoint
  call)
- **Durability**: Append-only, no data loss or mutation
- **Portability**: Log files travel with the project

## Log Entry Schema (Configurable)

### Slim Entry (default)
```json
{
  "turn_id": "string (Claude session turn ID)",
  "timestamp": "ISO 8601 string",
  "summary": "1-2 line human-readable summary",
  "refs": {
    "commit": "git commit hash (optional)",
    "files": ["list of file paths touched (optional)"],
    "tools": ["list of tools used (optional)"]
  }
}
```

### Rich Entry (when configured)
Slim entry + full turn context:
```json
{
  ...slim fields...,
  "context": {
    "input": "user prompt/query",
    "output": "claude response summary",
    "tools_called": ["tool1", "tool2"],
    "tool_outputs": "brief summary of tool results"
  }
}
```

## Integration Points

### Claude Code Hooks
- Post-turn hook: Triggered after each turn execution
- Resume hook: Detect session resume, load existing log, continue appending

### Summarization Endpoint
- Abstract interface (implementation TBD: Ollama, llama.cpp, Claude Haiku, etc.)
- Input: Recent log context (last N entries) + current turn context
- Output: 1-2 line summary string
- Must be local (no external API calls to preserve token efficiency)

## Deferred (Post-MVP)
- Viewing/querying UI (initially: append-only file, human-readable JSON)
- Log retention & cleanup policy
- Export to other formats (markdown, CSV, etc.)
- Search/filter across multiple logs

## Success Criteria
1. Reduced token usage: Benchmark shows <20% of claude-mem's cost
2. Context richness: New session can resume accurately from log + metadata
3. Easy resumption: Seamless pick-up without re-reading full history
4. Proven superiority: Comparative benchmarking vs. existing tools
