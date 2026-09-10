# 0010 — `NUMERIC` is declared without precision or scale

**Date:** 2026-09-10
**Status:** accepted

## Context
`latitude`, `longitude` and `area_ha` are `Decimal` because areas are
summed and compared against a parcel total, and binary floats do not
survive that. The type map turns `Mapped[Decimal | None]` into `NUMERIC`
on both backends.

The two `NUMERIC`s are not the same thing.

PostgreSQL's `NUMERIC` without arguments is arbitrary precision and
stores exactly what it is given. SQLite has five storage classes and none
of them is decimal; the declared type is accepted as a word, the value is
stored as `REAL`, and SQLAlchemy converts it back on read using
`decimal_return_scale`, which defaults to ten places.

Measured, on the current schema:

    written                    read back              equal
    45.771234              ->  45.7712340000          yes
    123456.1234            ->  123456.1234000000      yes
    0.12345678901234567890 ->  0.1234567890           no
    1.0000000000000001     ->  1.0000000000           no

`typeof()` on those rows returns `real`, and the last value is held in
the file as the integer `1`.

The first two survive. That is not luck and it is not the storage being
adequate — it is that `Field` caps coordinates at six decimal places and
`area_ha` at ten digits with four places, and those bounds sit well
inside what a float64 holds exactly.

The obvious tightening is `Numeric(9, 6)` and `Numeric(10, 4)`, matching
the Pydantic constraints.

## Decision
Bare `Numeric`. No precision, no scale.

The Pydantic constraint is already the owner, and a second copy of the
same numbers in a second place is `0009`'s argument unchanged: they are
kept in step by hand until the day they are not.

**This case is worse than the enum case, and that is why it is decided
the same way but recorded separately.** A vocabulary mismatch under a
native enum type fails the `INSERT` — loud, immediate, findable. A scale
mismatch under `NUMERIC(9, 6)` does not fail. PostgreSQL rounds to the
declared scale and commits. Raise `decimal_places` to eight in `Field`,
leave the column at six, and `45.77123456` is stored as `45.771235` with
no error anywhere. The value returned is not the value sent, and nothing
in the system says so.

Exceeding the declared *precision* does raise; exceeding the *scale*
rounds. The dangerous half is the one that stays quiet.

## Consequences
Values written through `Field` round-trip intact on both backends. They
do so because of where the Pydantic bounds happen to fall, not because
this layer protects them, and `db/` protects nothing by design — it
stores what it is handed. A `FieldRow` constructed directly with more
precision than `Field` would accept is truncated on SQLite without a
word.

**The dev/production difference is reduced here, not removed.** `0009`
made both backends do the same thing; this decision does not, and cannot.
Postgres stores decimals, SQLite stores floats, and no column declaration
changes that. What the decision does is keep the difference at the
storage layer instead of adding a second, contradictory rule on top of it.

Values read back from SQLite are padded to ten decimal places.
`Decimal("45.771234") == Decimal("45.7712340000")` is `True` and Pydantic
strips trailing zeros before counting places, so the round trip through
`Field` passes. `repr()` and `str()` differ. Any test that asserts on the
textual form of a `Decimal` rather than on its value will fail on one
backend and pass on the other — assert on equality, not on spelling.

**Revisit trigger:** the first arithmetic done in SQL rather than in
Python. `SUM(area_ha)` executed by SQLite is float addition, and at that
point the detour stops being incidental and starts producing the answer.
The same applies if SQLite is ever used for anything but tests. Either
way the fix is the backend or the query, not a tighter column.
