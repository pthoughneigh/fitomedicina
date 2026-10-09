# 0014 — The model keeps cadastral parcels sorted

**Date:** 2026-10-09
**Status:** accepted

## Context
`Field.cadastral_parcels` is a `list[str]`. `0011` stores the parcels as
rows with no column for order and reads them as a set, so the database
hands them back in whatever order it chooses. A list compares in order,
though, and until now only one way into a `Field` put the parcels in any
order at all: `to_field` sorted them on the way back from the database.

Every other way in kept the order it was given. Measured:

    Field(cadastral_parcels=["1234/6", "1234/5"])
      == Field(id=<same>, cadastral_parcels=["1234/5", "1234/6"])    False

The same land, the same parcels, typed in a different order, and the two
values are unequal. The round trip shows the same thing: a `Field` built
with its parcels out of order, written through `to_field_row` and read
back through `to_field`, does not equal itself.

The sort in `to_field` could not even be observed on SQLite. SQLite loads
a field's parcels through the composite primary key and returns them
sorted on its own: with the sort removed, parcels written as
`["1234/6", "1234/5"]` still came back as `["1234/5", "1234/6"]`.
PostgreSQL promises no order.

## Decision
`Field` sorts its parcels itself, in a `field_validator` on
`cadastral_parcels` that returns `sorted(value)`. Every way a `Field`
comes to exist goes through it: construction, assignment under
`validate_assignment`, and the read through `to_field`, which builds the
model with `Field(...)` (`0013`). `to_field` no longer sorts. The rule
has one owner — the argument of `0009`, where two owners of one
vocabulary could not be kept in step — and `grid_cell` already works
this way.

Rejected:

- **Sorting only in `to_field`**, the previous state. It covers one way
  in out of three, and a hand-built `Field` disagrees with its own round
  trip.
- **Sorting in the test.** Comparing against a sorted copy makes the test
  pass and leaves two `Field` values for the same land unequal everywhere
  else that compares them.
- **`relationship(order_by=...)`.** The database would return the rows
  sorted, but a hand-built `Field` would still keep the order it was
  typed in, and the rule would have a second owner in `db/`.
- **A set type.** `frozenset[str]` has no order to disagree about, but it
  iterates in no fixed order either, so anything printed or written from
  it can change from run to run. And it collapses duplicates without a
  word: a parcel listed twice is an error the composite key from `0011`
  reports loudly (`UNIQUE constraint failed`), and a set would hide it.

## Consequences
The order is canonical, not meaningful. It is string order, so `1234/10`
sorts before `1234/9`; a display that wants cadastral order sorts for
itself.

The order a user typed is not kept. `0011` already gave it up: no code
depends on the first parcel being first, and if any ever does, that is a
column, not a sort.

This is not a tightening in the sense of `0013`. Nothing is rejected, so
no stored row becomes unreadable; every row read back simply arrives
sorted.

Changing the list in place, with `append`, skips the validator, as it
skips every validator. The order returns at the next construction or
assignment.

**The rule is tested in the model, without a database.** The round-trip
test also fails when the sort is removed, but only because SQLite returns
the parcels sorted. Measured with the rule removed and the database made
to return the parcels in the order they were written: the round-trip test
stayed green, and only `test_cadastral_parcels_are_kept_sorted_in_string_order`
failed.

**Revisit trigger:** the first code that needs the parcels in an order of
its own — a lease document, a cadastral display. The order becomes a
column then, as `0011` says, and this sort becomes the default for
records that carry none.
