# 0003 — UUIDv4 for entity identifiers

**Date:** 2026-08-24
**Status:** accepted

## Context
UUIDv7 carries a 48-bit millisecond timestamp prefix, so generated ids
increase over time and inserts land at the right edge of a B-tree index.
UUIDv4 is fully random, so every insert targets a random leaf page, causing
page splits and poor cache locality. For a primary key, v7 is the better
default.

`uuid.uuid7()` entered the standard library in Python 3.14. This project is
pinned to 3.13.7, chosen because CatBoost was the binding constraint on the
Python version (see the decision table in the project context). Third-party
packages provide v7 on 3.13, but that is a new dependency for a single
function call, against the rule of installing per checkpoint.

## Decision
Use `uuid4` via `default_factory` on every entity id. No third-party uuid
package.

## Consequences
Both functions return `uuid.UUID`, so the field type is unaffected and the
swap is a single line at each `default_factory`. The type is structural;
the generator is not.

Switching later leaves mixed versions in one column. Acceptable while there
is no production data — development data is gitignored and disposable. Once
real users exist, either migrate or leave existing rows at v4.

v7 embeds a readable creation timestamp. `Field` does not care. `Case` may:
its id can appear in a URL, and an id plus `grid_cell` would disclose that
someone within a 1.1 km cell had a problem at a specific moment, which
works against the reason `grid_cell` exists. If v7 is adopted, decide per
entity rather than globally.

**Revisit trigger:** moving to Python 3.14. Check CatBoost wheel
availability at that point, since CatBoost drove the 3.13 pin.
