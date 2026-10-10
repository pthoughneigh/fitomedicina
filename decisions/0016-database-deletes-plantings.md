# 0016 — The database deletes a field's plantings

**Date:** 2026-10-10
**Status:** accepted

## Context
A planting points at its field through `field_id`. With a plain foreign
key, and the SQLite pragma on, deleting a field that has a planting is
refused. Measured: `IntegrityError: FOREIGN KEY constraint failed`, and
both rows stay. That is safe, since nothing is left pointing at nothing,
but it blocks erasure: a farmer's request to be forgotten has to remove
the field and its plantings together.

Two places can carry that deletion. The ORM can, through a
`relationship` on `FieldRow` with a cascade, as the parcels do. Or the
database can, through `ON DELETE CASCADE` on the foreign key itself.

## Decision
`field_id` is `ForeignKey("fields.id", ondelete="CASCADE")`. The
database deletes the plantings whenever their field row is deleted,
whichever way the delete arrives.

Measured: `session.delete` on a field removes the field, its parcels
(the ORM's cascade) and its planting (the database's). A bulk
`delete(FieldRow)` sent through `session.execute`, which the ORM never
sees, removes the planting as well, on a field without parcels.

Rejected: a `relationship` cascade from `FieldRow`, as for the parcels.
The parcels got their relationship so that they are written and read
with their field — they are part of `Field` (`0011`) — and the cascade
came with it. Plantings are not part of `Field`; nothing writes or reads
them through it. A relationship kept only for deleting would also make
`FieldRow` name `PlantingRow`, and every use of `FieldRow` then fails
unless `fito.db.planting` has been imported — measured,
`InvalidRequestError: ... expression 'PlantingRow' failed to locate a
name` — so `fito.db.field` would have to import this module: the
side-effect import that `0015` declines. And it would cover only deletes
that pass through the ORM. A bulk delete bypasses the ORM's cascade, as
was measured for the parcels on 28 September.

## Consequences
**On SQLite the cascade lives and dies with the foreign-key pragma.**
Measured with an engine built without it: the field is deleted and its
planting stays, with no error. Erasure then leaves personal data behind,
silently. `build_engine` turns the pragma on for every connection, and
the foreign-key test proves it does; anything that opens a SQLite
connection some other way gets neither the check nor the cascade.

Two mechanisms now delete what hangs off one field: the ORM deletes the
parcels, the database deletes the plantings. A bulk delete of a field
that has parcels is therefore still refused, because nothing but the
ORM deletes parcels. The failure is loud, and nothing is left behind.

The rule is part of the table's DDL, and `create_all` writes DDL only
for tables that do not exist yet. A database created before this change
would need a migration to gain it — Alembic, checkpoint 5 (`0012`).

**Revisit trigger:** the first bulk delete of fields, most likely the
retention job that sweeps fields without a holding (§16). The parcels
get `ON DELETE CASCADE` then, beside the relationship that writes and
reads them.
