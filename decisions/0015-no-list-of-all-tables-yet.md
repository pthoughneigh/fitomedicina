# 0015 — No list of all tables until something needs all of them

**Date:** 2026-10-10
**Status:** accepted

## Context
A table exists for `create_all` only once its module has been imported:
subclassing `Base` registers the class in `Base.metadata`, and importing
`base` alone leaves the catalogue empty. With one table module the
question of who imports what never arose.

`plantings` makes it real. Its `field_id` points at `fields.id`, so a
catalogue holding `plantings` without `fields` cannot be built. Measured,
with only `fito.db.planting` imported:

    NoReferencedTableError: Foreign key associated with column
    'plantings.field_id' could not find table 'fields' with which to
    generate a foreign key to target column 'id'

The usual answer is one place that imports every table module. It has
been tried once already, by accident: `engine.py` carried an unexplained
`# noqa: F401` import of the field tables, so importing `build_engine`
registered them as a side effect. That hid the empty-database trap, and
it was removed; tables now register where they are used.

## Decision
No list of all tables yet. Each test imports the table modules it uses.

For tests the rule enforces itself. A test cannot use `PlantingRow`
without importing `fito.db.planting`, and a test that writes a planting
writes its field first, so it imports `fito.db.field` as well. The one
mistake left, a referenced table not imported, fails loudly and names
the table.

Rejected for now:

- **A package import in `fito/db/__init__.py`.** Importing anything
  under `fito.db` — `base`, `engine` — would register every table as a
  side effect: the `engine.py` import again, at the scale of the package.
- **A dedicated module that imports every table module.** The honest
  form, and probably the eventual answer. With no reader today it would
  be a list nobody checks, and a table added without updating it would
  go unnoticed until the code that needed it.
- **Back into `engine.py`.** Already removed once, for reasons that
  still hold: `build_engine` answers which database, not what tables.

## Consequences
**The schema a test sees depends on what was collected.** pytest imports
every test module before running any test, so a full run registers
every table that some test module imports, while one file run alone
registers only its own. Measured: a test module importing only
`fito.db.field` sees `cadastral_parcels` and `fields` when run alone,
and `plantings` too when run beside a module that imports
`fito.db.planting`. Tests pass either way; they do not see the same
database.

The quiet failure this decision leaves open belongs to code that needs
tables it does not use. A `create_all` at startup would build a
database missing whatever nobody imported, and Alembic's autogenerate,
which compares `Base.metadata` with the live database, would propose
dropping every table it cannot see.

**Revisit trigger:** the first code that needs every table without using
them — Alembic's `env.py` at checkpoint 5, an entry point that creates
the schema, or a test that needs a table it does not touch, whichever
comes first. The list goes where that reader is, and not into
`engine.py`.
