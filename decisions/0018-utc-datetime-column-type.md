# 0018 — A column type of our own stores moments as UTC

**Date:** 2026-10-15
**Status:** accepted

## Context
`Case.opened_at` is timezone-aware and in UTC (`0006`). The first round trip
of a case through the database brought it back naive. Measured: the same
microsecond, with `tzinfo=datetime.timezone.utc` going in and no `tzinfo`
coming out, so the two compared unequal and nothing raised.

SQLite has no type for a timestamp with a zone. SQLAlchemy's `DateTime`
writes it as text, digits only, and the zone is dropped on the way in.
`DateTime(timezone=True)` does not change this. Measured: SQLite ignores the
flag and returns the same naive value. PostgreSQL honours it and would create
a `timestamptz` column, so with that flag alone the tests on SQLite and the
deployment on PostgreSQL would return different things for the same column,
the divergence `0012` exists to keep out of the code.

A naive value is not a smaller problem than a missing one. It reads as a
moment, compares without raising, and is wrong by the reader's offset the
first time someone converts it as local time. `0006` rests on `opened_at`
never being naive.

## Decision
`fito.db.types.UTCDateTime`, a `TypeDecorator` over `DateTime`, used for
every column that stores a moment. `opened_at` is the first.

- **On write** (`process_bind_param`): `None` passes. A naive `datetime` is
  refused with `ValueError`. An aware one, of any zone, is converted to UTC
  and its zone is dropped, so the column holds digits that always mean UTC.
- **On read** (`process_result_value`): `None` passes. The digits get `UTC`
  attached with `replace`, not `astimezone`, which would read them as the
  machine's local time and move them.

The rule sits at the column, so it holds for every reader and writer, not
only for code that goes through `to_case`. SQLite and PostgreSQL store the
same thing: a plain timestamp holding UTC.

The type does not convert to anyone's local time. That is display, and it
needs the user's zone, which no model carries yet (`0006`).

Rejected:

- **`DateTime(timezone=True)` alone.** Correct on PostgreSQL, ignored on
  SQLite. The tests would pass or fail for reasons that do not hold in
  deployment.
- **Re-attaching UTC in `to_case`.** Covers only that one reader; anything
  reading the row directly still gets a naive value. And if the column were
  ever `timestamptz` on PostgreSQL, a value already carrying `+02:00` would
  be relabelled as UTC and silently shifted by two hours.
- **Treating a naive value as UTC on write.** A guess at the zone. The value
  would be stored two hours off whenever the guess was wrong, with no error.

## Consequences
**Naive values are refused everywhere a column uses this type**, including
from tests, fixtures and a future import path. Code that builds a moment by
hand has to give it a zone. `test_naive_opened_at_is_refused` holds this,
writing a `CaseRow` directly, since the model cannot produce a naive value.

**On PostgreSQL the column is `timestamp without time zone`, holding UTC.**
Anyone querying the database directly, outside the ORM, has to know that
the digits are UTC. Raw SQL that compares the column with `now()`, which
returns a value with a zone, has PostgreSQL convert using the session's
time zone. That comparison is correct only when the session is set to UTC.

**Nothing enforces the type on the next timestamp column.** A new column
written as plain `Mapped[datetime]` gets SQLAlchemy's `DateTime`, loses the
zone on SQLite, and fails only when its own round-trip test compares an
aware value with what comes back. Each moment-storing column needs that
test.

`cache_ok = True` is set because the type holds no state that would make
two instances differ. Without it, SQLAlchemy warns the first time the
column is used in a `WHERE`.

**Revisit trigger:** the first run against a real PostgreSQL database,
checkpoint 9 at the latest. Neither the round trip nor the refusal has been
measured there. Or the first need to store a moment with the offset it was
observed in, rather than as a UTC instant, which this type cannot represent.
