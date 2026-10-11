# 0017 — A case requires a planting; a planting requires only its crop

**Date:** 2026-10-11
**Status:** accepted

## Context
`Case.planting_id` is required. §16 call 4 says a case cannot require a
field, because §14 promises that a first-time visitor is helped with zero
uploaded data, and a required field reference makes that visitor
unrepresentable. A required planting is stronger than the field reference
that call rejected, since a planting implies a field. The two statements
cannot both stand, and the `cases` table cannot be written until one of
them gives way.

Call 4 protected a promise to the visitor: no signup, no upload, help
before any data entry. It did not protect the absence of a `fields` row,
and the promise can be kept with the row present. `Field.holding_id` is
already nullable for exactly this path. A first conversation can create
an anonymous field (country and, if given, a coarse location), a planting
on it, and the case, in that order and without the visitor seeing any of
it. Registration is a question of flow, not of schema.

The anonymous field is a real field, not a placeholder. It stands for the
actual ground the farmer's crop is growing on, about which almost nothing
is known yet. Each conversation gets its own row and its own UUID, and
the foreign key checks it like any other. `country` is its only required
attribute; everything else is `None` or its documented default. When the
farmer later names a place or a soil, it is written to that row and to no
other. On registration the row gains a `holding_id` and becomes theirs.

The alternative, a nullable `planting_id`, makes the case carry its own
crop, coarse location and growth stage. When a planting does exist, there
are then two sources for the same facts, and they can disagree. Keeping
them in agreement is a rule over two objects, which is the shape `0005`
moved out of the schema.

Keeping the reference required, however, moves the problem rather than
solving it. As built, `Planting` has three required attributes besides its
field: `crop`, `status` and `establishment_method`. The case of a farmer
who writes "what is this yellow on my pepper" names the first and neither
of the others. The conversation would then have to ask for them, or make
them up.

- **Making them up.** `TRANSPLANTED` follows from pepper only usually.
  `ESTABLISHED` follows from a reported symptom only usually: a question
  about last season's crop is `TERMINATED`, rot in storage is past
  harvest, and a seedling problem before transplanting sits on ground that
  is still `PLANNED`. A value that is right at a high base rate is a
  guess, which is what `0002` declines.
- **Asking for them.** Neither answer changes the diagnosis of a yellow
  leaf, so the questions fill columns rather than narrow the differential.
  And a farmer who declines to answer leaves no way forward: no planting,
  no case, no help. That is call 4 again, through the back door.

## Decision
`Case.planting_id` stays required. §16 call 4 is superseded. Its intent,
that a first visitor is helped before any data entry, is kept by the
anonymous field and planting the conversation creates.

`Planting.status` and `Planting.establishment_method` become nullable,
with `None` as the default. `None` means *not recorded*. It does not mean
any member of the vocabulary. This is the `drainage` pattern from `0004`:
an unrecorded value and a recorded one are two facts, with two
representations.

Rejected:

- **An `UNKNOWN` member in either enum.** A vocabulary of ways to establish
  a stand, with "nobody said" as one of the ways. Nullability is a
  property of the column, not of the value set (`0004`). A member would
  travel with the enum into every model that reuses it, and every `match`
  over it would have to handle a value that is not a method.
- **A default per crop.** That is the guess above, written into the
  schema.
- **One shared "anonymous" field that every anonymous planting points
  at.** A sentinel row: one representation that means both "this field"
  and "no known field" (§5). Unrelated farmers' stands would sit on the
  same ground. The area bound in `0005` would sum them. A location learned
  from one farmer could not be recorded without moving everyone else. And
  `0016` would turn one erasure request into the deletion of every
  anonymous planting in the system.
- **A default of `ESTABLISHED`.** §17 already rejected it: a default status
  contradicts a null date. `None` asserts nothing, so that reasoning does
  not reach it.

The validator gains one rule: **an establishment date requires an
establishment method.** The method is what tells the single date column
what it means. For pepper, sowing and transplanting are six to eight
weeks apart, so a date without a method is ambiguous in exactly the way
the column was designed to prevent. The reverse stays allowed: a method
without a date is incomplete, not wrong. A farmer who knows the date
knows whether they sowed or transplanted, so the rule rejects no real
answer. It goes into `_check_lifecycle_consistency`, as another pair of
values that contradict each other.

The `PLANNED`-with-a-date rule is unchanged. A `None` status with a date
passes: the date says the plants went in, not whether they are still
there.

`crop` stays required. It selects the knowledge pack, and without it there
is no differential diagnosis. Asking for it is a diagnostic question, not
a form field. A farmer who withholds it after being asked has reached the
limit of what the system can do, not a gap in the schema. In practice the
crop is almost always named unprompted.

The rule for the conversation: **ask only what changes the diagnosis.**
The schema accepts what the conversation learns along the way. It does
not set the conversation's questions.

## Consequences
A planting needs only `field_id` and `crop`. Neither has to be invented.

The §18 open item on what `Case` carries resolves with this record: crop,
coarse location and growth stage are reached through the planting, so
`Case` carries none of them itself.

**What the conversation learns later is written to the planting, not to
the case.** A case reads crop, protection, dates and status through its
planting, so it always sees today's values rather than what was known when
it was opened. An example: a case opened on 1 June about yellowing pepper
leaves, with `protection` at its default `OPEN`. On 15 June the farmer
mentions a tunnel and a transplanting date, and the planting is updated.
From then on, the June case reads as if the system knew about the tunnel
when it gave its advice. It did not, and the record no longer shows that.
`initial_message` is unaffected, since it is kept verbatim. Accepted for
now, because the system's current reasoning (the next advice, disease
risk) needs the best current picture of the stand, which is the updated
one.

**Downstream code may no longer assume a planting is in the ground.** The
risk worker reads `status` to decide whether a stand is exposed to the
weather. A `None` status is unknown, not `ESTABLISHED`, and the worker
has to say so in its confidence rather than defaulting silently. The same
holds for `establishment_method` wherever a date is interpreted.

**The schema no longer catches a missing status or method in an upload.**
Until now, a file without a `status` column failed at `Planting(...)`.
From now on, every row is accepted with `None`, silently. The import layer
has to decide what an upload must contain and report a missing column
itself (`0002`), as it already must for the area bound (`0005`). The
conversation and the import path apply different rules: the conversation
takes what it is given, and a file can be asked to be complete.

**`NULL` drops out of SQL comparisons without an error.** A query such as
`WHERE status != 'terminated'` returns no rows whose status is `NULL`,
because the comparison is unknown rather than true. A retention job, the
risk worker or a report written that way would silently skip every
planting with an unrecorded status, which means every anonymous one. The
correct form is `status IS NULL OR status != 'terminated'`. In Python,
mypy forces the `None` branch to be handled. In SQL nothing does, so
every query over `status` or `establishment_method` gets a test with a
`NULL` row in it.

**The same ground is recorded more than once.** A farmer who returns
without an account starts a new conversation and gets a new field, since
nothing says it is the same person on the same plot. Linking anonymous
conversations would mean tracking the visitor, which is what the
anonymous path promises not to do. The duplicates are the cost of that
promise, not a defect.

Every anonymous conversation leaves a field without a holding, and a
planting on it. The retention job in §16 already has to sweep such
fields. The plantings go with them through `0016`, and the cases follow
once `cases` cascades from `plantings`, which is decided with that table
and not here.

No existing test asserts that an omitted `status` or
`establishment_method` raises; the requirement was enforced by the type
alone, so relaxing it breaks nothing visibly. That silence is the reason
for two tests: an omitted status and method are accepted as `None`, and a
date with no method raises while a method with no date passes.

**Revisit triggers:**

- **Pepper seedlings.** A problem in a nursery tray, before transplanting,
  is on live plants that belong to no field yet: the field they are
  destined for is `PLANNED`. Where such a stand lives in the model is
  open, and the first real pepper season will raise it.
- **The risk worker.** If it cannot produce a useful forecast for a
  planting with a `None` status, that is a reason to ask the question in
  conversation. It is not a reason to restore a default.
- **The first question about what the system knew when it advised.** This
  covers evaluating diagnostic accuracy against later outcomes as well as
  answering a complaint. Through the planting, the record can only say
  what is known now. The likely answer is a snapshot of the planting's
  relevant attributes stored with each piece of advice, not a copy on the
  case.
