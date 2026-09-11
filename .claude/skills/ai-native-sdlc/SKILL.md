---
name: ai-native-sdlc
description: Run Claude Code work as an evidence-backed, human-governed lifecycle. Use when planning, implementing, reviewing, testing, deploying, or improving a code change; keep simple changes lightweight.
---

# AI-native SDLC

Run an evidence-backed loop of durable artifacts, automated evidence, and human judgment. Apply it proportionately: a small, low-risk fix can use a concise plan and test evidence; a consequential or cross-team change needs explicit, reviewable artifacts.

## Carry intent forward

Before making a material change, establish a shared record of:

- **Intent:** problem, desired outcome, affected users/systems, constraints, and unresolved questions.
- **Spec:** requirements and design decisions, including policy conflicts or risks that need an owner’s judgment.
- **Plan:** files or components affected, work order, risks, alternatives, and the proof that will demonstrate success.

If the workflow uses version control, tickets, or PRs, keep the applicable artifacts there and link them. Declare the source of truth for each artifact when multiple systems exist. Do not invent formal documents when the task’s scope does not justify them; preserve the same information in the task, issue, plan, or PR description instead.

Do not begin material implementation until the applicable plan is accepted by the accountable person. If implementation changes the plan, update the plan and make the departure visible.

## Build with operational knowledge and feedback

- Follow the repository’s `CLAUDE.md`, project instructions, and documented commands. Keep `CLAUDE.md` concise, version-controlled, and focused on repeat mistakes, commands, conventions, architecture boundaries, and ownership.
- Turn a policy that must be applied consistently into a focused Claude Code skill under `.claude/skills/` or an automated hook; leave repository-specific context in `CLAUDE.md` and one-off context in the current task.
- Give the implementation a tight feedback loop: run the build, relevant tests, lint/static analysis, and—when it matters—an observable behavior or visual check. Report the actual evidence, including limitations.
- For a defect, prefer first establishing a failing regression test or other reproducible proof. Fix the implementation rather than weakening the proof. If test changes are legitimate, explain why they are not masking the defect.
- Parallelize only independent work with isolated file ownership and a review capacity that can keep up. Keep coupled changes in one coordinated stream.

## Review at the right level

Review against the artifacts, not merely the diff. Separate findings into at least:

1. Behavioral defects and regressions.
2. Security, privacy, and reliability risks.
3. Compliance with the accepted intent, spec, plan, and repository standards.

Use automation for consistent mechanical review and ranking. Reserve human attention for intent, material risk, exceptions, and approval; an agent must not approve its own change. Keep findings, fixes, verification results, and approvals in the normal audit record.

## Increase autonomy only behind controls

Start a new agentic workflow manually. Automate triggers or subsequent stages only after the artifact, verification, approval, and rollback paths are reliable.

- Apply Claude Code permissions, sandboxing, scoped credentials, and environment-specific permissions to automation.
- Let automation prepare releases and act freely only in environments and scopes explicitly authorized by the user or organization. Production actions remain behind a named human gate unless an existing policy explicitly delegates them.
- Prefer allowlisted tools and pre-approved runbooks over broad shell or production credentials. Rehearse rollback before relying on autonomous deployment.
- Make gates explain their decision and leave an attributable, timestamped record.

## Close the learning loop

Use deterministic signals—tests, CI failures, alerts, tickets, or scheduled checks—to trigger investigation. Let the agent diagnose within its permitted scope, then write its evidence and proposed outcome back into the next intent or issue for ordinary review.

Treat `CLAUDE.md`, skills, hooks, and permissions as production configuration: evaluate meaningful real tasks when they change, gate regressions, and add incidents or escaped defects as lasting regression cases. When a recurring review finding or Claude Code mistake is confirmed, improve the appropriate durable guidance or check rather than relying on memory.
