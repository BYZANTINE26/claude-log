---
Status: accepted
---

# Log integrity: mark failures, never fabricate or silently drop entries

The scrapped branch's summarizer fell back to a rule-based placeholder
summary on any failure (endpoint down, timeout, malformed response), and
folded a crash-orphaned turn buffer silently into the next unrelated
turn's summary. Both corrupt the log's meaning without any trace. Instead,
any failure — summarization failure or a stale buffer found from a
previous crash — is written as an explicit marker entry
(`"summary_failed": true` or `"turn_lost": true`) with no fabricated
summary text, and surfaced to the user via a `systemMessage` at the point
of failure.

## Considered Options
- Silent fallback summary (rejected — the original bug: fabricated
  content indistinguishable from a real summary during deep-dive review).
- Silent skip, no log trace at all (rejected — an unexplained gap looks
  identical to "nothing happened this turn," misleading later).

## Consequences
The log can contain entries with no summary text, only a marker — any
consumer (viewer, benchmarking tooling, a future summarization pass) must
treat `summary_failed`/`turn_lost` as a distinct, expected entry shape.
