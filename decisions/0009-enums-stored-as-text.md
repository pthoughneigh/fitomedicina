# 0009 — Enums are stored as text, never as a database enum type

**Date:** 2026-09-10
**Status:** accepted

## Context
`DeclarativeBase` carries a type map from Python annotation to SQL type.
`Mapped[uuid.UUID]` becomes `CHAR(32)` without anyone writing `CHAR` or
`32`; the map is where that happens.

The map's default entry for enums resolves to `sqlalchemy.Enum`, and that
type does not produce the same thing on both backends. PostgreSQL gets a
type of its own — a `CREATE TYPE ... AS ENUM` statement, and a column
declared as that type. SQLite has no such facility and falls back to
`VARCHAR`.

So one annotation produces two different databases. The stricter of the
two is the one nobody runs locally: the suite is green on SQLite whether
or not the vocabularies agree, and the disagreement surfaces only in
production.

This is the same shape as the unnamed constraints that `SQL_NAMING_CONVENTION`
exists to prevent. A decision left to the backend gets made twice, and
differently, and the divergence is invisible from the machine where the
work happens.

A second question opens as soon as the column is plain text. An enum
member has a name and a value — `CHERNOZEM` and `chernozem` — and once
the database no longer knows the type, something has to choose which of
the two is written down. `sqlalchemy.Enum` writes the name by default.

## Decision
One entry on `Base.type_annotation_map`, keyed on `enum.Enum`, mapping to
`SAEnum(enum.Enum, native_enum=False, values_callable=enum_values)`.

`native_enum=False` forces `VARCHAR` on every backend. No `CREATE TYPE`,
no column-level vocabulary, nothing for the database to disagree with.

`values_callable` persists the member's **value**, not its name. The
values are the external code lists — ISO 3166 alpha-2, WRB soil groups,
USDA texture classes — and those are the strings that mean something
outside this repository. The names are Python identifiers that happen to
be uppercase because that is how enum members are written.

Keyed on `enum.Enum` rather than on each concrete enum, so the rule
covers `SoilType`, `Slope`, `Crop` and every enum not yet written. Per
enum, the entry that is forgotten is the one that silently gets a native
type in production.

The rule sits beside `SQL_NAMING_CONVENTION` because it is the same kind
of rule: one place, project-wide, the code decides and not the backend.

## Consequences
The database enforces no vocabulary at all. `Field` is the only owner of
what a valid `SoilType` is, which is the point — two owners cannot be
kept in step, and the day they drift there is no answer to which one is
right. A widened enum in Python is a code change and nothing more; under
a native type it would be a migration against a live database.

**The name-versus-value choice is invisible on the first column that
uses it.** `Country.RS` has the value `"RS"`; name and value are the same
string and no test can tell them apart. The first column where they
differ is `soil_type`, and there `values_callable` is the difference
between a round trip that works and a `ValidationError` on read. Setting
it now rather than discovering it later is the whole reason this is
written down.

Column width follows the longest member: `VARCHAR(2)` for `Country`,
`VARCHAR(15)` for `SoilTexture`. Adding a member longer than the current
longest changes the column and needs a migration. Bare `TEXT` would avoid
that, at the cost of reading back a plain `str` where the annotation
promises an enum member — a lie in the type, which this project does not
write. The migration is the cheaper of the two.

`create_constraint` defaults to `False` in SQLAlchemy 2.x, so no `CHECK`
is emitted. **Do not turn it on.** A `CHECK` listing the permitted
strings is the same second owner arriving through a side door, and it
would look harmless in review.

**Revisit trigger:** a value in the database that no enum member matches,
found weeks after it was written. That is the failure this decision
accepts, and if it happens the question is where the check belongs —
most likely at the import boundary described in `0002`, not in the
column. Moving it into the database would mean accepting the migration
cost that was declined here, and should be argued as such rather than
added quietly.
