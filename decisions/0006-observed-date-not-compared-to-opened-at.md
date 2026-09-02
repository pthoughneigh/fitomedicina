# 0006 — `observed_on` is not compared to `opened_at`

**Date:** 2026-09-02
**Status:** accepted

## Context
A symptom is seen before it is reported. The rule holds without exception,
and `Case` carries both halves of it: `observed_on`, the day the farmer
noticed something, and `opened_at`, the moment the case entered the system.
An `observed_on` later than `opened_at` is a data entry error.

This looks like the date ordering rule on `Planting` and is not. There both
dates are `date` and both are agronomic: sown on one day, terminated on
another, the same kind of fact twice. Here the two fields are different
kinds of time. `opened_at` is machine time, known to the second, recorded
in UTC. `observed_on` is what a person read off their own calendar. They
are not two dates; they are a timestamp and a human day.

Comparing them means converting one to the other, and the conversion needs
a timezone the model does not have. A report at 23:30 local is still the
previous day in UTC, so a farmer answering "today" correctly would be
rejected. A one-day tolerance would paper over this at UTC+1 and stop
working immediately outside it — Russia alone spans eleven zones, and the
region is deliberately not fixed.

The timezone belongs to the person or the holding, not to the problem they
are reporting. `Case` has no route to it, and giving it one would mean
validation could no longer be performed on an object built from data alone
— the same objection that moved the field area rule out of the schema in
0005.

## Decision
No comparison between the two fields. `opened_at` is
`datetime.now(UTC)` via `default_factory`, timezone-aware rather than
naive, so the instant survives a second region being added.

`Case` therefore has no `model_validator` at checkpoint 2. That is the
outcome of the reasoning above, not an omission.

## Consequences
Nothing rejects an `observed_on` in the future. A mistyped year is stored
and read downstream as the start of the weather window the risk worker
reasons over. Acceptable while data is disposable; the first real upload
surfaces it.

A model with two time fields and no rule between them reads as an
oversight, and the obvious fix — `if self.observed_on > self.opened_at.date()`
— is one line and silently wrong outside UTC+1. This record exists to stop
that line being written.

Storing UTC also means no local date can be recovered from `opened_at`
alone later. Nothing is lost that was ever held: the local offset was never
recorded, and inferring it from `grid_cell` would use a coarsened location
for a purpose it does not exist for.

**Revisit trigger:** the first model that carries a user's timezone —
a holding, an account, or whatever the import path turns out to need. The
rule becomes writable at that point, and belongs wherever that value lives
rather than back in `Case`.
