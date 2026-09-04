# 0008 — `Crop` stays at two members; `preceding_crop` records the gap

**Date:** 2026-09-04
**Status:** accepted

## Context
`Crop` carries two meanings that have not yet been separated. One is the
set of crops the system can diagnose: the value selects the knowledge
pack, and a member with no pack behind it is a promise the system cannot
keep. The other is the set of crops that grow on land, which is far
larger and includes crops this system will never diagnose.

`Planting.crop` wants the first. `preceding_crop` wants the second. They
share a type because until now they had the same two members.

So `preceding_crop: Crop | None` can record only `wheat` or `pepper`.
The column's own justification names the smallholder's 2025 cabbage as
the case it exists for, and cabbage is not a member. The load-bearing
agronomic case is worse: wheat after wheat is a fusarium prior and wheat
after soybean is not, and soybean cannot be written down. The column
cannot hold the example that argued for it.

Four routes were considered.

Widening `Crop` now means choosing members with no upload, no user and
no file to choose them against.

A second, wider enum is not available in the form it first suggests: an
enum with members cannot be subclassed, so a wider set means a second
list maintained by hand beside the first. The functional API sidesteps
the subclassing error but hides the members from mypy, which removes
the reason the enum exists under `strict = true`.

Free text (`str | None`) makes the column work immediately and fits the
`0002` route from raw value to code list. It was rejected on one
requirement: the column must reject what it does not recognise. Free
text also puts the first unclassifiable-at-design-time attribute on
`Planting`, which until now is entirely agronomic — "the cabbage my
neighbour Milan gave me" is a preceding crop and a personal datum.

A vocabulary file in `data/`, read at startup and checked at runtime,
satisfies every requirement at once and follows the rule already set in
§17: agronomic values live in `data/` with a citation per row and a
test, or they do not exist. A crop list is an agronomic fact; a
two-member `Crop` is a statement about this system's capability and
belongs in code. It is the right answer eventually and its contents
would be guessed today.

## Decision
Change nothing. `Crop` keeps `WHEAT` and `PEPPER`. `preceding_crop`
stays `Crop | None`.

The column is kept rather than dropped. Its values are perishable in a
way `Case.status`'s were not: a farmer knows the rotation today and
nobody reconstructs it a year later. A column with no reader whose data
is lost if it is absent is not the same as a column with no reader that
predicts a workflow.

**No `UNDEFINED` member, and no sentinel of any other spelling.** `None`
already means "not recorded", completely and without ambiguity. This is
`0004` inverted: there the danger is one representation carrying two
facts, here it would be two representations carrying one. Every future
check written as `is None` would have to be `is None or == UNDEFINED`,
and the first reader who writes only half of that gets a silent wrong
answer.

An enum member is a valid answer; a null is the absence of one, and the
database knows the difference — a null does not group and does not
count in `COUNT(column)`, while a sentinel string appears in preceding-
crop statistics as a category and enters a model as a level.

A member would earn its place only for a genuine third state: the
farmer was asked and said they do not know, as against never having
been asked. Those are two facts. No flow asks, so the member has no
referent — field by referent, as with `Case.status`.

## Consequences
The column cannot record the case that justifies it. It is a place
held, not a working attribute, and that has to be legible at the
attribute rather than only here, or the next reader sees a two-member
enum on a rotation column and closes the gap in five minutes in
whichever direction occurs to them first.

Whatever first reads this column reads it as report-don't-reject: an
absent or unrecognised preceding crop means the prior is unavailable,
never an error. Same shape as the unchecked plantings in `0005`.

Nothing is spent by waiting. No table exists, no upload path exists, no
data is at risk, and the members chosen at the revisit will be chosen
against a real file instead of against an imagination.

**Revisit trigger:** the first real upload of plot history, or the
first user whose preceding crop is neither wheat nor pepper. The choice
then is between the `data/` vocabulary and a widened enum, made against
the file in hand. Taking the vocabulary route carries a second decision
with it: "can this be diagnosed" stops being a type and becomes a
knowledge-pack lookup, which moves the failure from construction time
to diagnosis time and makes the message better rather than worse. It
also settles the same debt `Slope`'s undecided breakpoints carry — an
agronomic fact currently living where nothing can test it.
