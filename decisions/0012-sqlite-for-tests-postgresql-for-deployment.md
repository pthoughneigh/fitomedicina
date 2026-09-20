# 0012 — SQLite in the test suite, PostgreSQL in deployment

**Date:** 2026-09-14
**Status:** accepted

## Context
This split was never decided. §9 lists it — SQLite locally, PostgreSQL
deployed, one codebase via SQLAlchemy — and nothing ever argued it. It
arrived as an assumption and has been in force since the first table.

By now it has cost three records, and only one of them says so.

`0009` exists because `sqlalchemy.Enum` resolves to a native `CREATE TYPE`
on PostgreSQL and to `VARCHAR` on SQLite. `0010` exists because PostgreSQL
rounds a value past the declared scale and commits it, while SQLite has no
decimal storage class at all and sends the value through a float. The
foreign-key pragma exists because PostgreSQL enforces a foreign key and
SQLite ignores it until asked, per connection.

Three records, three unrelated-looking subjects, **one difference found
three times.** None of them looked like a dialect question on arrival, and
the pattern was invisible until they stood next to each other.

`engine.py` is where the choice stops being a footnote. The function takes
a URL, and the URL *is* the dialect — so the first backend-specific
condition in the project lands here.

## Decision
The split is kept. SQLite in the suite, PostgreSQL in deployment.

It buys two things. `uv run pytest` needs nothing installed and nothing
running — no Docker daemon, no service, no credentials — so the suite works
on any machine that can check out the repository. And an in-memory database
is built and thrown away per test at a cost that keeps the suite worth
running on every commit.

**The alternative was a real PostgreSQL in the suite**, through Docker. It
tests what actually ships, which is the thing this decision gives up. It
was rejected on setup cost and speed, not on principle: it makes a green
suite depend on a daemon being up, and it makes the first run on a new
machine a configuration problem rather than a command.

That is a trade, and it is recorded here so it is not mistaken for an
oversight.

## Consequences
**The suite does not test the database that ships. Green is not proof.**

What the suite cannot see, per record:

- `0009` — a native `ENUM` rejects an `INSERT` carrying a value outside the
  type. SQLite accepts any string. The suite passes whether or not the
  vocabularies agree, which is the failure `0009` was written to close by
  removing the native type entirely.
- `0010` — the two backends cannot be made to agree here at all, and `0010`
  says so explicitly. Values read back from SQLite are padded to ten
  decimal places, so `repr()` differs across backends while `==` holds.
  Assert on equality, never on spelling.
- The pragma — until it is attached, a parcel pointing at a non-existent
  field inserts cleanly. A suite that looks like it tests a constraint and
  does not is worse than no test.

The general cost: **anything that must hold on PostgreSQL and cannot be
observed on SQLite gets argued in prose instead of asserted in a test.**
Three records so far are exactly that, and reasoning is weaker than
execution. Expect more of them, and expect them to arrive looking like
something else — none of the three announced itself as a dialect problem.

## Revisit trigger
**Alembic, at checkpoint 5.**

Alembic generates a migration by diffing `Base.metadata` against a *live*
database. If that database is SQLite, the diff is shaped by what SQLite can
report about itself — which is considerably less than PostgreSQL, and least
of all about constraints. The resulting migration then runs against
PostgreSQL.

At that point the divergence stops being contained in a test suite and
enters a committed file that alters a database holding data. That is the
qualitative change, and it is why the trigger is Alembic rather than the
first deployment: by deployment every migration has already been written
blind, and a review then records damage instead of preventing it.

`SQL_NAMING_CONVENTION` was written for that day before Alembic existed
here — constraint names are chosen by the code because a migration can drop
a constraint only by name. It is consistent that this record wakes up in
the same place.

**The trigger does not mandate the move.** It means the argument is run
again with the accumulated cost visible, which it is not today. Same shape
as `0003` checking CatBoost wheels on the day Python 3.14 is considered,
rather than committing to the upgrade in advance.
