# 0013 — Stored rows are read back through `Field`, not around it

**Date:** 2026-09-28
**Status:** accepted

## Context
`to_field` turns a `FieldRow` back into a `Field`, the reverse of
`to_field_row`. Pydantic offers two ways to build the model from the
row's values. `Field(...)` runs every validator again, exactly as when
the value was first built. `Field.model_construct(...)` runs none: it
writes the values it is given straight onto the instance, as
`model_copy(update=...)` does.

Both were run against rows the model would never have written.

`grid_cell` overwritten on disk with raw SQL —
`UPDATE fields SET grid_cell = 'garbage'` — and read back:

    FieldRow                     'garbage'
    Field(...)                   '45.77,19.35'
    Field.model_construct(...)   'garbage'

A `FieldRow` written directly, bypassing `Field`, with a latitude of
eight decimal places against the model's six, and read back:

    FieldRow                     Decimal('45.1234567800')
    Field(...)                   ValidationError: decimal_max_places, ('latitude',)
    Field.model_construct(...)   Decimal('45.1234567800')

The two results are one distinction seen twice. `grid_cell` is
derived: the validator computes it from the coordinates, so a read
through the validators recomputes it and discards the stored value.
`latitude` is recorded: someone wrote it down, nothing can compute it,
and a validator can only accept or reject it. A validated read
therefore repairs derived values silently and refuses recorded values
that today's rules reject.

The second case is not hypothetical. `FieldRow` stores what it is
handed, by design, and a rule tightened on `Field` after rows exist
turns every stored row it rejects into exactly that row. The likeliest
next rule is already known: a regional bound on coordinates, because
global bounds pass transposed latitude and longitude. The demo for this
record transposed them by accident, and nothing objected.

One thing that looks like a third case is not. SQLite hands decimals
back padded to ten places (`0010`), and `Field(...)` accepts them:
Pydantic strips trailing zeros before counting places, so
`Decimal('45.7712340000')` satisfies `decimal_places=6`. A validated
read does not trip on the padding.

## Decision
`to_field` builds the model with `Field(...)`. `model_construct` is not
used on the read path.

The two layers already give both honest answers. `FieldRow` is the disk
as it is, with no promises — it read the eight-decimal latitude without
complaint. `Field` is a value that satisfies every rule the model
states. `model_construct` makes a third thing: the disk's contents
under the model's name. In both runs it returned an object of type
`Field` that breaks `Field`'s own rules — a `grid_cell` contradicting
its coordinates, a latitude the field constraint forbids — and nothing
on the object says so, while every reader of a `Field` relies on
exactly those rules. That is a lie in the type, which `0009` already
declined for enums. It adds nothing a `FieldRow` does not provide
except the false label.

Code that needs the stored values as they are reads `FieldRow`. Code
that receives a `Field` can trust it, whichever way it arrived.

Rejected as well: `Field(...)` with a fallback to `model_construct`
when validation fails. Every reader of the model would again be unable
to tell which kind of `Field` it holds, and the failure that says a row
and a rule have diverged would be swallowed instead of reported.

## Consequences
**Derived values are recomputed on every read, silently.** The disk can
hold a different `grid_cell` from the one the application sees, and
nothing reports the difference. Anything that reads the column
directly, below the model, sees the disk's version.

For `grid_cell` this is also protection. If the cell rule ever changes
— coarser cells, say, because 1.1 km turns out to identify someone —
every `Field` read carries the new cell at once, instead of old cells
being served from disk until a migration catches up.

A stale derived column is refreshed from the model, because the model
recomputes it. Writing the value back is an update to an existing row,
and that path does not exist yet: `session.add` of a second row with
the same `id` fails on the primary key (on SQLite,
`UNIQUE constraint failed: fields.id`).

**A tightened rule makes the stored rows it rejects unreadable, and
loudly.** `to_field` raises `ValidationError` on them. That is the
intended failure, not one to catch and paper over.

So a rule on `Field` is no longer tightened by editing the model alone.
The tightened rule lands together with a fix of the rows it would
reject, or after it — never before. The fix is made on the rows
themselves: the round trip cannot make it, because `to_field` refuses
exactly the rows that need fixing. Which value is correct is decided
per case. Eight decimals truncate to six with no loss that matters;
coordinates are swapped back only once they are known to have been
transposed.

**Revisit trigger:** the first rule on `Field` tightened while stored
rows exist that it would reject — most likely the regional coordinate
bound — or Alembic at checkpoint 5, whichever comes first. That is when
the row fix stops being a sentence here and becomes a migration.
