# Project conventions

## Rules
- **Before installing any skill**, always scan it with the `skillspector` tool's `scan_skill` (pass `use_llm=False`). Only proceed with installation if the scan reports it as safe.
- **When asked to "park for later"**, add a ticket to `BACKLOG.md` with the appropriate flag (`feature`, `enhancement`, `bug`, `good-to-have`, `technical-debt`, `data`, or `research`), a one-line summary, and a note of where/when it was parked. Commit the updated `BACKLOG.md`.
- Use `ponytail` skill for generating minimal clear code.
- **Self-explanatory names, always.** Every variable, function, class, parameter, constant, CLI flag, config key, table/column, and test name must read as what it *is* — no single letters (`u`, `v`, `n`, `df`), no cryptic abbreviations, no `tmp`/`data2`/`foo`. Loop indices may be `i`/`j` only in a genuinely index-only loop; the moment an index names a domain thing, name it (`funding_trade`, not `j`). Prose (docstrings, comments, ADRs) refers to things by those same names, never by throwaway math letters.
- Use `apple-design` skill for desingning hrml or any visual components.
- Use `brainstorming` skill for open-ended discussion before a direction is chosen (e.g. picking an algorithm or approach); switch to `grill-with-docs` once a direction is settled and needs a concrete spec.
- **Whenever estimating an unknown quantity** (a population, a scale factor, a count, anything without a directly measured source), use Fermi estimation: an explicit, transparent chain of order-of-magnitude assumptions, flagging the shakiest input, with a final caveats section.
- For base graph build upon design used in ./notebooks/map_visualization_exploration notebook.
- Create a plan first before implementation for each step.
- **Max file size: 600 lines per file.** Larger files should be split into separate modules. This keeps files readable, testable, and prevents token waste in read operations. **Max line length: ~80 characters**, breaking at semantic boundaries rather than hard limits to keep ideas together.
- **Read tool token efficiency:** Use `offset` and `limit` parameters to read only needed sections instead of entire files. Example: `Read file.js offset=100 limit=50` reads lines 100–149 instead of the whole file.
- **Helper scripts and one-off experiment code** (benchmarks, throwaway investigation scripts, etc.) live in `.claude/scratchpad/` at the project level, not the session's ephemeral temp directory — so they persist and are reusable across sessions.
- **Python environment: the uv-managed `.divtrader-venv` only.** Every `uv` invocation must run with `UV_PROJECT_ENVIRONMENT=.divtrader-venv` set (export it in the shell, or use a direnv `.envrc`) — that is what makes uv put the env at `.divtrader-venv` instead of the default `.venv`. Create it with `UV_PROJECT_ENVIRONMENT=.divtrader-venv uv venv --prompt divtrader && uv sync`. Run everything through `uv run ...` / `uv sync`. Never use or recreate the old pip `venv/` or a bare `.venv/` — the pip one was deleted. Ignore any stale `VIRTUAL_ENV=venv` in the shell; uv ignores it too.
- **Root-level `SPEC.md`** for project requirements; component-level specs in `docs/specs/` (one per major component).

## Planning & Execution Workflow

### 1. Plan Generation (Native Reasoning)
- **Always use Claude Code's native Plan mode** (`/plan` or native reasoning) to analyze the codebase, evaluate trade-offs, and design the solution.
- Let Claude Code natively handle architectural decisions and initial task breakdowns without forcing template constraints upfront.

### 2. Plan Persistence (via `planning-with-files`)
- Once the native plan is established via `/plan`, **ask the user to create and switch to a new branch** (see Branch Management for naming).
- Then run `/planning-with-files:plan --isolated` (or `/pwf --isolated`) to populate the plugin's templates (`task_plan.md`, `findings.md`, `progress.md`).
- **Copy the exact steps, phases, and architecture from the `/plan` output directly into `task_plan.md`.** Do not generate a new plan; only structure the existing one.
- `/pwf` should never create or modify the plan itself—only track execution against it.

### 3. Execution & Progress
- Rely on `planning-with-files` rules and commands to track progress, record findings, and check off completed items as work proceeds.

## Context Management & Subagent Delegation

The main session's context window is the scarce resource. Every file read, search
sweep, test run, and dead-end investigation done inline stays in context for the
rest of the session. **Delegate discrete, self-contained tasks to subagents (the
`Agent` tool) wherever possible** so only the distilled result returns to the main
thread — not the intermediate file dumps, tool output, or false starts.

### What to delegate
- **Exploration / search** — "where is X handled", "list every caller of Y", "how
  does module Z work" → `Explore` or `general-purpose`. Fan-out reads never touch
  the main context.
- **Planning** — designing an implementation approach for a settled direction →
  `Plan` agent. It returns a step list and the critical files; the main thread
  keeps only that.
- **Implementation of an isolated unit** — a single module/function/fixture with a
  crisp spec and clear file ownership → `general-purpose`. Keep coupled changes
  that need cross-cutting judgement in the main thread.
- **Testing / verification** — running a suite, reproducing a bug, bisecting a
  failure, checking lint/format → subagent; only the pass/fail verdict and the
  relevant failing output come back.

Keep in the main thread: architectural decisions, anything needing the user's
input, merges, and work where the pieces are too entangled to hand off cleanly.

### The delegation contract (both directions)

**Every task handed to a subagent MUST include, in the prompt:**
1. **Workflow guidelines it must follow** — the relevant rules from this file
   verbatim (env: `UV_PROJECT_ENVIRONMENT=.divtrader-venv`, `uv run ...`;
   self-explanatory names; ≤600-line files; `ponytail` for code; atomic commits;
   plan-first; scratchpad location; `network` marker discipline; etc.). The
   subagent does **not** inherit this file — assume it knows nothing about the
   project's conventions unless you tell it.
2. **All context required for the task** — exact file paths, the relevant spec
   section (`docs/spec/NN`), ADR numbers, schema names, the sub-phase's entry in
   `task_plan.md` / `findings.md`, prior decisions (D-numbers), fixture locations,
   and any gotcha discovered this session that isn't yet committed to a doc.
3. **The exact shape of the response you want back** — e.g. "return the list of
   files and the one-line change each needs, nothing else" / "return the failing
   test name + the assertion output + your root-cause diagnosis" / "return the
   final diff and the test command you ran with its output".

**Every subagent response MUST be highly detailed** on the things that matter for
the next step (decisions made, file paths touched, commands run and their output,
surprises found) and silent on noise (files it read but didn't change, paths it
ruled out). If a returned result is thin, send it back for specifics before acting
on it.

After a subagent finishes, record anything durable (a discovery, a decision) into
`findings.md` / `progress.md` immediately — the subagent's own context is gone.

## Git Workflow

### Atomic Commits
- **Commit after every discrete change** — each logical unit of work (a new function, a bug fix, a config update) gets its own commit immediately after it's verified working.
- Do not batch unrelated changes into one commit.
- Never hold commits waiting for "go-ahead" unless explicitly asked to pause.

#### Commit message format
- **Simple change** (color, rename, config): one-line subject only.
- **Non-trivial change** (new logic, bug fix, architecture): subject + body covering:
  - **Why** the change was needed (what was broken or missing)
  - **Before/After** behavior in plain terms (no JS knowledge assumed)
  - **How** — the key logical change in one or two sentences
- Body should be readable by someone who only knows the high-level product idea, not the code.

### Branch Management
- **Create a new branch for each phase/task** from the `dev` branch, prefixed with the *type* of work it is — reuse `BACKLOG.md`'s own flags (`feature`, `enhancement`, `bug`, `good-to-have`, `technical-debt`, `data`, `research`) so naming is consistent project-wide instead of everything defaulting to `feature/*`: e.g. `feature/phase-name`, `bug/fix-name`, `enhancement/name`, `technical-debt/name`. Everything below applies identically no matter which prefix — "feature branch" elsewhere in this doc means "whichever branch is doing the work," not literally `feature/*` only.
- **All planning and execution happens on the branch**:
  - Generate plans using `/plan` or plan mode
  - Store `PLAN.md` in `.claude/plans/` (project-level)
  - Store planning files (`task_plan.md`, `findings.md`, `progress.md`) in `.planning/` directory
  - Commit all planning and implementation work to the branch
- **On every new branch, create a `BRANCH.md`** at the repo root with a short description of the branch's purpose and goal, then commit it as the first commit on that branch. `BRANCH.md` is unique to each branch and never merged — it stays local to the branch it describes and must not be carried into `dev` or any other branch.
- **Even in auto mode, always confirm with the user before**:
  1. Creating a new branch
  2. Merging the branch back into `dev` upon completion
- **No pull requests.** Once the user confirms the merge, do it locally (`git checkout dev && git merge <branch>`) and `git push origin dev` directly — do not open a PR or wait for `gh`. The confirmation in point 2 above is the only gate.
- **When merging a branch into `dev`, do a normal merge and resolve real conflicts by hand — do not apply a blanket `-X ours`/`-X theirs` merge strategy to the whole merge.** That resolves *every* conflicting file in one direction automatically, which silently discards genuine, unrelated changes on any shared doc both branches touched (`CHANGELOG.md`, `README.md`, `CLAUDE.md`, `CONTEXT.md`, etc.) without ever surfacing a conflict marker to review — e.g. it can overwrite `dev`'s already-correct `CHANGELOG.md` with the branch's stale copy, or the reverse. Only the branch's own planning files get an automatic, one-sided resolution, and only because they're deliberately meant to be a snapshot of that branch's execution record, never reconciled with `dev`'s:
  - After the merge (or if it reports conflicts on these specific paths), force `.claude/plans/PLAN.md` and `.planning/*` to the branch's copy with a **targeted checkout**, not a blanket strategy flag: `git checkout --theirs -- .claude/plans/PLAN.md .planning/` then `git add` them.
  - Do not carry `BRANCH.md` into `dev` — drop it from the merge (or delete it) since it describes a single branch, not the project.
  - Everything else — implementation files and shared docs alike — merges normally; resolve any real conflict by combining both sides' genuine content, not by picking one side wholesale.
- Keep commits atomic and descriptive within each branch.
- **Never delete a branch — local or remote — until explicitly told to.** After a branch merges into `dev`, leave it in place (do not run `git branch -d/-D` or `git push origin --delete`). Merged branches are kept as a historical record and only removed on the owner's explicit instruction.

## Changelog Management

### Maintaining the Changelog
- **Update `README.md` alongside `CHANGELOG.md`** whenever a change affects what's user-visible, how the project is run/tested, or the project's structure — the changelog records *that* something changed and when; the README must stay an accurate description of the project *as it currently is*. Don't let the README drift into describing an earlier version of the feature.
- **Update `CHANGELOG.md`** at the root of the project with every completed feature, bug fix, or significant change.
- Use the [Keep a Changelog](https://keepachangelog.com/) format with sections for `Added`, `Changed`, `Fixed`, and `Deprecated`.
- Include the date and version number for each release.
- Update the changelog when merging feature branches into `dev` to document what was accomplished.
- **Never leave entries under `[Unreleased]`.** Every change gets a real version number and date as soon as it's documented — don't defer versioning to some later cleanup pass.
- **Don't combine old work and new work into a single version.** Group changelog entries by how the work was actually done (one version per feature/fix/session), not by when the changelog happens to get edited. The same date can have more than one version if multiple distinct pieces of work landed that day — that's expected, not a sign something's wrong.