Store ADRs in `docs/adr/` as sequentially numbered files, for example `0001-event-sourced-orders.md`.

```md
# {Short title of the decision}

{One to three sentences covering the context, decision, and why it was chosen.}
```

Use only this title and paragraph unless an optional section preserves non-obvious context:

- `Status` frontmatter: `proposed`, `accepted`, `deprecated`, or `superseded by ADR-NNNN`
- **Considered Options**, when rejected alternatives are worth remembering
- **Consequences**, when downstream effects are non-obvious

Consider ADRs for architectural shape, inter-context integration, lock-in technology choices, ownership or boundary decisions, deliberate deviations from the obvious path, non-code constraints, and non-obvious rejected alternatives. Apply the three ADR criteria in the main skill before creating one.
