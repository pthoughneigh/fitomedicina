# 0005 — Field area is validated in the import layer, not in the schema

**Date:** 2026-08-29
**Status:** accepted

## Context
A field's `area_ha` should bound the plantings on it: the areas of the
stands occupying a field at one time cannot exceed the field itself. The
reverse is not a rule — a field can be partly fallow, so the sum is an
upper bound and not a derivation.

Neither model can enforce it. `Field` holds no reference to its plantings;
the foreign key runs the other way and will stay there. `Planting` holds a
`field_id`, but that is a UUID — checking the rule from a planting's
validator means loading the field and every sibling planting, which puts a
database read inside schema validation. Validation would stop being
constructible from data alone, the test suite would need a database, and a
single object could no longer be built without its context.

The rule is not about an object. It is about a set: one field and the
stands on it at one moment.

"At one moment" is load-bearing. Wheat sown in October 2025 and harvested
in July 2026, followed by maize sown in May 2026, are both 4 ha on a 4 ha
field. Their naive sum is 8 ha and nothing is wrong. Simultaneity has to be
read from `establishment_date`, `termination_date` and `status`.

Those dates are deliberately nullable (see the validator on `Planting`), so
some stands cannot be placed in time at all.

## Decision
The rule lives in the import layer, alongside the alias table from 0002.
Not in either model's validators, and not in a validator that reads the
database.

Plantings that cannot be placed in time are excluded from the sum and
reported as unchecked, rather than being assumed simultaneous or assumed
absent. Due at checkpoint 5, with the import path.

## Consequences
Until then nothing prevents a 4 ha field carrying three concurrent 3 ha
plantings. Development data is disposable, and the error surfaces on first
upload rather than silently.

The import layer already has to accumulate errors per file rather than
raise per object (0002). A set-level rule fits that shape and would not fit
a per-object validator, which is a second reason it belongs there.

This does not revisit the nullable dates. A schema that demanded an
establishment date would get invented ones — indistinguishable from
recorded ones, and read downstream as growing degree days. A tolerant
schema can be tightened later; invented data cannot be cleaned. The cost is
that this rule cannot check every planting, and that cost is visible in the
report rather than hidden in a number.

**Revisit trigger:** a second set-level rule appearing. One belongs in the
import layer; several are a validation service, and that is a different
decision.
