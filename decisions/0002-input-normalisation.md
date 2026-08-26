# 0002 — Input normalisation lives in the import layer

**Date:** 2026-08-24
**Status:** accepted

## Context
Uploaded files carry free text where the schema expects code-list values:
`Srbija`, `Србија`, `serbia`, `RS`. The enums accept only `RS`. Something
has to bridge the two, and there are two candidate homes: a Pydantic
validator with `mode="before"` on the model, or the import layer that reads
the file.

## Decision
Normalisation happens in the import layer, before a model is constructed.
The schema stays strict and knows only code-list values.

The bridge is a closed alias table — an explicit dict, looked up after
`.casefold()`, including the already-correct spelling so there is one code
path and not two. No fuzzy matching. Unrecognised values are collected and
reported per file, not guessed.

Rejected: a `mode="before"` validator on the model. Two reasons. It raises
per object, so a 214-row upload with twelve bad cells yields twelve
sequential exceptions instead of one report. And it would make
`Field(country="Srbija")` succeed from internal code, which weakens the
invariant that a `Field` in memory always holds a `Country` member.

## Consequences
Validation and normalisation stay separate concerns: the enum answers
"is this permitted", the alias table answers "what did the human mean".
A wrong guess here shows a user a product not registered where they farm,
so guessing is not an acceptable failure mode.

A new spelling is a one-line commit to the alias table.

The import layer must accumulate errors rather than raise on the first one.

The alias table is not written yet. It needs a real upload path to have a
referent, and the spellings people actually type are better observed than
invented. Due at checkpoint 5.

The same shape will be needed for crop names, but those are Serbian domain
content and belong in the knowledge pack, not the import layer.