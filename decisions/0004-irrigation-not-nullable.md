# 0004 — `irrigation` is not nullable, `drainage` is

**Date:** 2026-08-24
**Status:** accepted

## Context
`Field.irrigation` and `Field.drainage` are near-identical in shape: an enum
whose `NONE` member records a surveyed absence. They are deliberately typed
differently.

`drainage: Drainage | None = None` — `NONE` means there is no artificial
drainage, `None` means nobody has recorded it. Two facts, two
representations.

`irrigation: Irrigation = Irrigation.NONE` — the unknown case collapses into
the surveyed-absence case.

The asymmetry is easy to read as an oversight and "fix" by making both
nullable. This record exists to stop that.

## Decision
Keep `irrigation` non-nullable with `Irrigation.NONE` as the default.
Rain-fed is the regional base rate, so an unrecorded field is assumed
rain-fed rather than unknown.

Source: Statistical Office of the Republic of Serbia, 2023 Census of
Agriculture — 8.3% of utilised agricultural area was irrigated in the
2022/2023 agricultural year, over a UAA of 3,239,373 ha.

(The Office's separate annual irrigation survey reports a far smaller
absolute area, because it covers only legal entities and cooperatives —
0.4% of holdings. The census figure is the one that describes this
project's users.)

## Consequences
Missing data is silently readable as a surveyed fact for this one attribute.
Any analysis that counts rain-fed fields is counting unknowns alongside them
and cannot separate the two afterwards. Acceptable at a ~92% base rate;
not acceptable for `drainage`, which has no comparable figure.

**The default is the common case, not the safe case, and here they differ.**
Assuming rain-fed means assuming less leaf wetness, which biases fungal
disease risk downward. The stated asymmetry for this system is that missing
an outbreak costs a field while a false alarm costs one spray, so the error
this default makes is on the more expensive side. Accepted because the base
rate is strong and because irrigation is a capability a user can state in
one question; revisit if the risk worker turns out to be sensitive to it.

**Revisit trigger: paprika, around month four.** The base rate above is over
all agricultural land, which is dominated by arable field crops. Vegetable
production under tunnels is a different population and much more likely to
be irrigated, so a default derived from the national figure may be wrong for
exactly the crop this system is being built for. If the default becomes
crop-dependent, it stops being a schema default and moves to the knowledge
pack.

The justification lives as a comment on the `Field.irrigation` attribute,
not in the `Irrigation` docstring. The enum is a vocabulary and may be
reused by a model that makes it nullable; nullability is a property of the
column, not of the value set.
