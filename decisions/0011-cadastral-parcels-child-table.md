# 0011 — Cadastral parcels are rows, keyed on `(field_id, parcel_number)`

**Date:** 2026-09-10
**Status:** accepted

## Context
`Field.cadastral_parcels` is `list[str]`. The firm in §16 holds twenty-three
of them on one field. A relational column holds one value, so the list
cannot be stored as written and something has to give.

Three routes were available.

A delimited string — `"1234/5,1234/6"` — works until the first question
that asks which field contains parcel `1234/5`, which is then a text
search that hopes no parcel number contains the delimiter. It fails
silently when one does.

A JSON column is honest about holding a list and is portable across both
backends. It leaves the same question expensive: finding one parcel means
reading every row in `fields` and unpacking each list.

A child table, one row per parcel, answers the question directly and is
the shape the data already has.

Given a child table, the key is a second question. A surrogate `id` per
row works. A composite key on `(field_id, parcel_number)` also works and
does one thing more.

## Decision
A `cadastral_parcels` table: `field_id` with a `ForeignKey` to
`fields.id`, `parcel_number`, and those two columns as the primary key.
No surrogate `id`.

Three reasons pull the same way, and none of them is storage size.

Leases change, and in practice that means adding one parcel and removing
another. Against rows that is an `INSERT` or a `DELETE`. Against a list
it is rewriting the whole collection on every edit, correctly, every time.

The parcel number is an external join key. The cadastre and the subsidy
registry both work by it, so the question "which field is this parcel"
is one this project will be asked.

Parcel numbers are personal data and are listed as such in §5. An erasure
request has to reach them. A row is deleted; an element inside a JSON
document is located and the document rewritten.

**The composite key is the one rule this project adds to the database
rather than declining to.** `0009` and `0010` both refused a second
owner because Pydantic already held the constraint. Here it does not and
cannot: `Field` validates one field at a time and has no view of the
table, so the same parcel arriving on the same field through two separate
writes is invisible to it. Under a surrogate key those are two rows with
different ids and identical meaning, and the database accepts them
without comment. A duplicated parcel is the same land declared twice —
it inflates any area or subsidy figure computed from these rows, and
nothing in the output says a number is wrong.

The rule goes where the gap is, not where the cover already exists.

## Consequences
A `Field` is no longer one row. Translation between model and storage
spans two tables in both directions, and the parcel rows have to be
written and read as part of the same unit of work as the field.

**Order is lost.** `list[str]` has one and a table does not; rows come
back in whatever order the query produces unless one is asked for. This
is accepted on the reading that the parcels are a set rather than a
sequence — no current code depends on the first parcel being first. If
something ever does, that is a column, not an assumption.

**SQLite does not enforce the foreign key by default.** It is capable of
it and ships with it off, per connection, for backwards compatibility.
Until `PRAGMA foreign_keys=ON` is issued on connect, a parcel pointing at
a field that does not exist inserts cleanly on SQLite and fails on
PostgreSQL — the same silent divergence as `0009`, arriving through the
connection rather than the schema. This is the first thing that goes into
`engine.py`. Written down here because a suite that looks like it tests
the constraint, and does not, is worse than no test.

The composite key means a parcel row cannot be referenced from elsewhere
by a single value, and renaming a parcel number is a delete and an insert
rather than an update.

**Revisit trigger:** a parcel gaining attributes of its own — lease start
and end, area, tenure — at which point it stops being a link and becomes
an entity, and an entity with a two-column identity is awkward to
reference. The surrogate `id` comes back then, with a unique constraint
on the pair to keep what this decision bought. Also revisit if the same
parcel number legitimately appears twice on one field, which would mean
`parcel_number` is not identifying what it is assumed to identify.
