---
name: brainstorming
description: Interactive, small-back-and-forth discussion for open-ended problems where the approach isn't chosen yet — e.g. "how should I think about X", "is there a better algorithm for this", picking a strategy before any spec exists. Use when the user wants to think out loud or explicitly asks to discuss/brainstorm, not when they've already picked a direction and want it nailed down.
---

# Brainstorming

Think out loud together, one small step at a time, before any direction is chosen. This is the *earlier* stage than `grill-with-docs`: that skill front-loads a whole question frontier to converge fast on a spec once a direction is picked. Brainstorming is for when the problem itself isn't framed yet, several directions are genuinely plausible, and converging too fast would foreclose a better idea before it's considered.

## Behavior

- **One thing per turn.** A single question, a single trade-off, or a single option to react to — never a wall of text or a batch of questions to get through at once.
- **Lean, don't decide.** Offer a recommendation as a starting point to react to, not a decision being ratified. The user can reject it and redirect entirely — that's the point.
- **Cap alternatives at 2–3 named options**, one line of reasoning each, when comparing approaches. Not an exhaustive survey of every option that exists.
- **Let the answer reshape the next turn.** Don't pre-plan the whole conversation — the next question depends on what the user just said, not a fixed script.
- **Keep it short.** If an explanation would run past a few sentences, cut it and offer to expand only if asked.
- **Direction changes are normal, not a failure.** E.g. genetic algorithm → simulated annealing mid-conversation. Chase the better idea, don't defend the earlier one.
- **Close by summarizing the settled direction in a few lines and confirming it** before handing off to `grill-with-docs` (to nail down the concrete spec) or straight to planning, if the problem is simple enough not to need one.

## When NOT to use

- The user already picked a direction and wants the concrete details settled — use `grill-with-docs` instead.
- The task is a small, unambiguous fix — just do it, no discussion needed.
