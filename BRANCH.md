# Branch: feature/claude-log-load-compiled

## Purpose

Implements `BACKLOG.md #22`: a `--compiled` flag for
`/claude-log-load [count] [--compiled]`. Instead of printing the last
`count` summaries line-by-line, sends them to the configured
summarization endpoint to be consolidated into one narrative.

## Design decisions

- **Fallback, never a hard failure.** No endpoint configured, or the
  compile call fails for any reason → silently falls back to the normal
  numbered-list output. Same philosophy as `summary_failed` markers:
  a degraded-but-present result beats an empty one or an error.
- **Argument parsing.** `SKILL.md` passes `"$ARGUMENTS"` as one quoted
  shell word, so `claude_log/cli.py` can't rely on `sys.argv` being
  pre-split — `_parse_arguments` splits that single string itself,
  order-independent (`--compiled 5` and `5 --compiled` both work).
- **Reused `summarizer.py` plumbing.** `call_openai_compatible_endpoint`
  and `call_claude_code_provider` were refactored to take a generic
  `(system_prompt, user_content)` instead of the turn-summarization-
  specific args, so `compile_summaries()` reuses the same HTTP/subprocess
  code and the same never-fabricate-on-failure contract as `summarize()`,
  via a shared `_call_endpoint` dispatcher.

## Scope

- `claude_log/summarizer.py`: `compile_summaries()`, `_COMPILE_SYSTEM_PROMPT`,
  `_build_compile_content()`, the `_call_endpoint` refactor.
- `claude_log/cli.py`: `_parse_arguments()`, `compiled` param on
  `load_recent()`.
- `skills/claude-log-load/SKILL.md`: documents the flag.
- No change to `record_reingestion`/window-growth bookkeeping — `count`
  still means the same thing either way.
</content>
