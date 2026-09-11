Write `CONTEXT.md` in this form:

```md
# {Context Name}

{One or two sentences describing the context and why it exists.}

## Language

**Order**:
{One or two sentences defining what the term is.}
_Avoid_: Purchase, transaction

**Invoice**:
A request for payment sent to a customer after delivery.
_Avoid_: Bill, payment request
```

Keep `## Language` flat until natural term clusters justify subheadings.

For a multi-context repository, write `CONTEXT-MAP.md` with each context, its `CONTEXT.md` location, and their relationships:

```md
# Context Map

## Contexts

- [Ordering](./src/ordering/CONTEXT.md): receives and tracks customer orders
- [Billing](./src/billing/CONTEXT.md): generates invoices and processes payments

## Relationships

- **Ordering → Billing**: Ordering emits `OrderPlaced`; Billing consumes it to create invoices.
```
