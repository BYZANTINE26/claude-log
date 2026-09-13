# Backlog

- **[technical-debt] #1** No file locking on the session log — two Claude Code
  sessions sharing a `session_id` would corrupt `<project>/.claude-log/logs/
  <session_id>.jsonl` since writes aren't coordinated across processes. Parked
  2026-09-11 during the Core Logging MVP's first planning pass; single-writer
  is an accepted assumption for now (see `docs/specs/core-logging.md`).

- **[technical-debt] #2** No rotation or retention policy on the per-session
  summarized logs (`<project>/.claude-log/logs/<session_id>.jsonl`,
  `claude_log/logger.py::append_entry`) — they grow unbounded for the life
  of a session. Not to be confused with `~/.claude-log/internal.log`, the
  plugin's own operational log, which already rotates
  (`claude_log/config.py::get_logger`'s `RotatingFileHandler`). Parked
  2026-09-11.

- **[technical-debt] #3** `refs.commit_before`/`commit_after` become dangling
  references if the commit is later amended, rebased, or reset — the stored
  hash no longer resolves to anything in `git log`. Parked 2026-09-13 during
  the grill-with-docs redo (`docs/adr/0004-drop-rich-mode-and-tool-call-tracking.md`);
  accepted as the same class of limitation as any commit-hash-based audit
  trail.

- **[enhancement] #4** `get_recent_entries` re-reads the whole JSONL log file
  every turn to compute the tail slice — fine at MVP scale, but should switch
  to a seek-from-end read once logs grow large enough for this to matter.
  Parked 2026-09-13, `docs/specs/core-logging.md`.

- **[feature] #5** Real local summarization model behind the OpenAI-compatible
  `/v1/chat/completions` contract (see `SPEC.md`'s Integration Points and the
  reference request shape in `docs/specs/core-logging.md`) — the HTTP client
  is real, only "which model to run" is deferred to the user's own setup.
  Parked 2026-09-11.

- **[feature] #6** Benchmarking suite comparing claude-log vs. claude-mem on
  token usage, context fidelity, and resumability — its own phase post-MVP,
  tracked as an `INTENT.md` success criterion, not blocking Core Logging.
  Parked 2026-09-11.

- **[good-to-have] #7** Viewing/querying UI or CLI for browsing a session log.
  Parked 2026-09-11.

- **[good-to-have] #8** Export a session log to markdown/CSV; search/filter
  across multiple session logs in a project. Parked 2026-09-11.

- **[good-to-have] #9** Compression/encryption for archived log files. Parked
  2026-09-11.

- **[research] #10** A real end-to-end test run (subagent, `--plugin-dir` +
  a throwaway test project, `/Volumes/GBC/projects/test_claude_log`) hit
  one `files: []` result on a genuine edit-only turn (editing an already-
  created `hello.txt`) that could not be reproduced in 3 follow-up
  attempts of the same create-then-edit sequence, and predates the
  separately-found-and-fixed untracked-directory bug
  (`claude_log/git_snapshot.py::_hash_paths`, see CHANGELOG). Recorded
  as an unexplained one-off, not a confirmed bug — revisit if it recurs
  with a reproducible trigger. Parked 2026-09-13. A second independent
  re-test on 2026-09-13 (fresh throwaway project
  `/Volumes/GBC/projects/test_claude_log_v2`, 5 repeated create-then-edit
  attempts) also failed to reproduce it — still unexplained, still not
  blocking, ticket stays open in case it recurs with a real trigger.

- **[research] #11** How a prompt queued before the prior turn's `Stop` fires
  sequences against that turn's `prompt_id` is still undocumented (whether
  `UserPromptSubmit` for the queued prompt can fire before the earlier
  turn's `Stop`). Confirmed separately, directly from the hooks reference's
  own Stop section: `Stop` does **not** fire on a Ctrl+C interrupt at all
  (API errors go to `StopFailure` instead), so the interrupt case is no
  longer a research item — `docs/adr/0006-prompt-id-keyed-turn-buffers.md`'s
  `turn_lost` orphan sweep is confirmed necessary, not hypothetical.
  Partially exercised 2026-09-13 in the real end-to-end test run: two
  `--resume <same session_id>` invocations launched back-to-back showed
  no corruption or interleaving at the JSONL or buffer-file level, each
  getting its own correctly-separated buffer and log entry — but this is
  concurrent headless resumes, not confirmed proof of the interactive
  "prompt queued while the model is still generating" scenario the
  question is actually about. Parked 2026-09-13, still open.

- **[enhancement] #12** `~/.claude-log/internal.log`'s `debug`/`info` levels are
  currently dead weight — `claude_log/config.py::get_logger`'s level
  filtering and rotating handler work correctly, but no code path calls
  `logger.debug(...)` or `logger.info(...)` anywhere; only `warning`
  (`summarizer.py`: no endpoint configured) and `error` (each hook's
  caught-exception handler, `summarizer.py`'s failed endpoint call) are
  ever logged. Found 2026-09-13 while reviewing why the independent
  post-fix re-test's `internal.log` had zero new lines despite
  `log_level: "debug"` being set — expected, since the re-test hit no
  failures, but it means `debug`/`info` currently show nothing even when
  set. If pursued: log each hook's entry/key decision (buffer started,
  git snapshot taken, summarization call made) at `debug`, successful
  turn completion at `info`, so the level setting is actually meaningful.
  Parked 2026-09-13, not blocking — the log's original purpose (crash/
  failure diagnostics) is unaffected.

## Publish

Findings from a 2026-09-13 gap analysis (grounded in `plugins.md`,
`plugin-marketplaces.md`, `plugins-reference.md`, and `hooks.md`, fetched
directly rather than assumed) on what's required to ship claude-log as a
plugin anyone can install through Claude Code, not just load locally via
`--plugin-dir` or hand-clone into `~/.claude/skills/`.

- **[feature] #13** No marketplace distribution — claude-log currently
  only loads via `--plugin-dir` (a dev/test flag) or by manually cloning
  into `~/.claude/skills/claude-log/` (the skills-directory route chosen
  deliberately in `docs/adr/0001` for personal use). `/plugin install
  claude-log@<marketplace>` — the actual "anyone installs through Claude
  Code" flow — requires a `.claude-plugin/marketplace.json` (repo root or
  a separate marketplace repo) listing claude-log with a `source` (e.g.
  `{"source": "github", "repo": "BYZANTINE26/claude-log"}`), hosted on
  GitHub. Optionally, submit to the public `claude-community` marketplace
  via the in-app form so users don't need to add a custom marketplace
  first — this runs `claude plugin validate` plus automated safety
  screening. Parked 2026-09-13, not started.

- **[technical-debt] #14** `plugin.json` is missing fields expected for a
  public listing: `repository`, `homepage`, `license`, `keywords` (all
  optional per the manifest schema, but expected for discoverability and
  user trust). There is also no `LICENSE` file anywhere in the repo — a
  real blocker for anyone deciding whether they're allowed to use or
  redistribute it. Parked 2026-09-13.

- **[bug] #15** Cross-platform hook invocation is unverified and likely
  broken on Windows. `hooks/hooks.json` invokes each hook as a bare path
  in shell form (no `args`), e.g. `${CLAUDE_PLUGIN_ROOT}/claude_log/hooks/
  session_start.py`, relying on the `#!/usr/bin/env python3` shebang plus
  the executable bit (confirmed `100755` in git). This works on
  macOS/Linux but standard python.org installs on Windows don't put a
  `python3` executable on `PATH` (only `python.exe`/`py.exe`), so `env
  python3` resolution can fail outright even under Git Bash. `hooks.md`
  recommends exec form (`"command": "python3", "args": ["${CLAUDE_PLUGIN_ROOT}/
  claude_log/hooks/session_start.py"]`) for anything with a path
  placeholder — more portable, avoids quoting bugs — but doesn't by
  itself resolve the `python3`-vs-`python` naming gap on Windows. Needs a
  real decision (detect the interpreter at runtime? document Python
  3.10+ with `python3` on `PATH` as a hard prerequisite? add a `py`/
  `python` fallback?) before this can be called production-ready for a
  general audience. Parked 2026-09-13.

- **[technical-debt] #16** File locking (`#1` above) was an accepted
  MVP-scale limitation for a personal single-user tool. For a plugin
  anyone installs, running two Claude Code sessions on the same project
  (two terminals, or a main session plus a subagent-spawned one) is a
  common real pattern, not an edge case, and would corrupt the shared
  `.jsonl` log under concurrent writes. This should be resolved (even a
  simple `fcntl`/`msvcrt` advisory lock beats none) or at minimum
  prominently documented as a known limitation before a public release,
  not left silent. Parked 2026-09-13, supersedes/elevates `#1` for the
  publish effort specifically.

- **[technical-debt] #17** All testing to date (unit suite plus both real
  end-to-end runs) has been on macOS only. No Windows or Linux
  verification exists. Given `#15`, this isn't just a formality — running
  the plugin for real on Windows would likely surface a genuine bug, not
  just confirm a formality. Parked 2026-09-13.

- **[research]** Tickets `#10` (unreproduced `files: []` anomaly) and
  `#11` (queued-prompt sequencing) are low-stakes for a single careful
  user but more likely to surface as confusing bug reports once install
  numbers go up. Not necessarily blocking for an initial 0.x public
  release, but worth another look before declaring a stable 1.0. No new
  ticket number — cross-referencing the existing entries above.

- **[good-to-have] #18** `${CLAUDE_PLUGIN_DATA}` (the plugin-lifecycle
  -managed persistent directory that Claude Code deletes automatically on
  uninstall) isn't used — claude-log deliberately stores its config and
  internal log at `~/.claude-log/` instead (`docs/adr/0002`). That's a
  fine design choice, but it means uninstalling the plugin will *not*
  clean up `~/.claude-log/`; the README should say so explicitly so a
  user doesn't wonder why config/log files persist after uninstall.
  Parked 2026-09-13.
