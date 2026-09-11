---
name: grill-with-docs
description: Relentlessly stress-test a plan, decision, or design in a round-based interview, while documenting settled domain language in CONTEXT.md and consequential decisions as ADRs.
---

Before asking questions, read `CONTEXT-MAP.md` if it exists; otherwise read the root `CONTEXT.md` if present. Use the map to identify the relevant context. If the topic could belong to multiple contexts, ask the user which one applies.

Build a **design tree**: each decision is a node and each dependent decision is a child. The **frontier** is every unresolved decision whose prerequisites are settled. Treat facts available from the repository, environment, or tools as investigation tasks, never as user questions.

## Rounds

Ask the entire frontier in one response. Number each question, give a clear recommendation, then wait for the user's answers:

```md
❓ **Q1 — <title>**: <question, context, and meaningful choices>

➡️ <recommended answer and brief rationale>

---

❓ **Q2 — <title>**: <question, context, and meaningful choices>

➡️ <recommended answer and brief rationale>
```

After each answer:

- Record settled decisions and recompute the frontier.
- Ask the next whole frontier; never ask a question whose answer relies on another question still open in the same round.
- Find facts yourself. Delegate a bounded investigation to a subagent when useful. While it is pending, block only the dependent branch and continue with the remaining frontier.
- Surface conflicts between the user's claims and the code or existing documentation. Ask which should govern instead of silently reconciling them.
- Challenge fuzzy, overloaded, or inconsistent terms. Propose a precise canonical term and use concrete edge-case scenarios to test domain boundaries.

End only when the frontier is empty. Summarize the shared understanding and ask for confirmation. Do not start implementation until the user explicitly asks.

## Glossary

Update the relevant `CONTEXT.md` as soon as a domain term is resolved; do not batch edits.

- Create `CONTEXT.md` only when the first project-specific term is resolved. In a single-context repository, it belongs at the root; in a multi-context repository, use the relevant location from `CONTEXT-MAP.md`.
- Keep the glossary free of implementation details, scratch notes, and decisions.
- Define what a term *is*, not what it does, in one or two sentences. Choose one canonical term and list competing terms under `_Avoid_`.
- Include only concepts specific to this project's context, not general programming terminology. Group terms under subheadings only when natural clusters emerge.
- If the user uses a glossary term with a conflicting meaning, resolve the conflict before proceeding.

For a new or substantially changed glossary, read [the context format](references/context-format.md).

## ADRs

Offer an ADR only when all three conditions hold:

1. The decision is hard to reverse.
2. It would be surprising to a future reader without context.
3. It resulted from a real trade-off among alternatives.

When the user agrees, create the ADR immediately in the relevant `docs/adr/` directory. Create the directory only for the first ADR. Scan it for the highest existing number and use the next four-digit number. Keep ADRs short; add optional sections only when they preserve non-obvious context. Before writing, read [the ADR format](references/adr-format.md).

Skip routine, reversible, obvious, and choice-free decisions.
