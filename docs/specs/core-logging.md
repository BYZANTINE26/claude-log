# Component: Core Logging

## Purpose
Manage session logging lifecycle: create/resume logs, coordinate with
summarization endpoint, persist log entries to disk, and ensure session
resumability.

## Responsibilities
- Detect session identity (Claude session ID) and project context
- Create or resume log file in `.claude/logs/` directory
- Coordinate post-turn hook execution
- Collect turn context (input, output, tools used, files touched, commit hash)
- Call summarization endpoint with recent log context + current turn
- Append entry to log file in atomic write
- Provide interface for consumers to query/resume from log

## Data Model

### Log File Location
```
.claude/logs/session_<session-id>.jsonl
```
- One JSONL file (JSON Lines format) per session
- Filename includes session ID for uniqueness and resumability
- Path is deterministic and project-scoped

### Log Entry (see SPEC.md for full schema)
- Immutable once written (append-only)
- Includes turn ID, timestamp, 1-2 line summary, refs (commit, files, tools)
- Optional: full turn context if Rich mode is configured

## Interface

### Public Methods

#### `initialize_or_resume(project_root: str, session_id: str, config: dict) -> Logger`
- Check if log file exists for this session
- If yes: open and prepare for append
- If no: create new file with header/metadata
- Load last N entries into memory for summarization context
- Return Logger instance

#### `log_turn(turn_data: dict) -> None`
- Accept turn data: input, output, tools_called, tool_outputs, files_touched,
  commit_hash
- Call summarization endpoint with (recent_log_context, turn_data)
- Get 1-2 line summary
- Build log entry (slim or rich based on config)
- Append to log file (atomic write)

#### `get_recent_entries(count: int = 10) -> list[dict]`
- Return last N entries from log
- Used for providing context to summarization endpoint

#### `close() -> None`
- Flush pending writes
- Cleanup temporary state

## Configuration

### Environment/Settings
```json
{
  "logging": {
    "enabled": true,
    "verbosity": "slim",
    "recent_context_window": 10,
    "summarization_endpoint": "http://localhost:11434/api/generate",
    "log_directory": ".claude/logs"
  }
}
```

## Integration Points

### Hook: Post-Turn Execution
- Claude Code hook fires after each turn
- Hook receives: turn_id, input, output, tools_used, tool_outputs
- Hook calls `Logger.log_turn(turn_data)`
- Hook monitors summarization latency (ensure <1 second)

### Summarization Endpoint
- Accepts: `{"recent_entries": [...], "current_turn": {...}}`
- Returns: `{"summary": "1-2 line string"}`
- Timeout: 5 seconds (fail-safe: generate fallback summary if timeout)

## Error Handling
- **Summarization endpoint unreachable**: Generate fallback summary ("Tool call:
  X returned Y bytes")
- **Disk write failure**: Log to stderr, notify user, continue session (log
  attempt is best-effort)
- **Malformed turn data**: Log what was provided, use generic summary
- **Session ID mismatch on resume**: Treat as new session (safety check)

## Testing Strategy
- Unit tests: Log entry creation, serialization, recent context retrieval
- Integration tests: Hook execution, summarization endpoint calls, file I/O
- Benchmarking: Token count comparison with claude-mem for equivalent turns

## Known Limitations
- Single-writer assumption (one Claude Code session per project at a time)
- No locking (concurrent access will corrupt log; out of scope for MVP)
- No log rotation (unbounded log growth; can add retention policy later)

## Future Enhancements
- Log rotation and cleanup (e.g., delete entries older than 30 days)
- Concurrent access via file locking or log sharding
- Compression for old entries
- Encrypted log files for sensitive projects
