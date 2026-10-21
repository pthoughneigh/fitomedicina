# 0020 — The knowledge pack is a TOML file in `knowledge/`

**Date:** 2026-10-21
**Status:** accepted

## Context
The narrowing loop needs to know, for one crop and one symptom, which
causes are possible, which questions tell them apart, and what each
answer rules out. §4 calls that a knowledge pack and says a crop is
configuration, not code. Checkpoint 1 needs the first one — four causes
of yellowing in wheat and three questions — and five things had to be
settled before it could be written: where it lives, in which folder, in
which format, what shape it takes, and what it says about its sources.

## Decision
**A data file, not code and not the database.** The picture is a car's
navigation. The program knows no road by heart; the roads are in a map,
which is a separate file, and a new country is a new map while the
program stays the same. The narrowing loop is the program and the
knowledge pack is the map. A new crop is a new file and the loop does
not change, which makes "a new crop absorbed in a week" (§4) a claim
about adding a file.

Rejected:

- **A Python module.** Nothing stops logic from creeping into one — "if
  this is pepper, skip this question" — and then the engine and the
  content grow into each other: the drift §4 warns about with one agent
  per crop, in another form. A data file cannot hold an `if`.
- **The database.** The database holds what farmers enter. The
  knowledge pack is written by us, and every change to it should show up
  in a commit with a reason, as a change to code does. In a table it
  would be an `UPDATE` with no history.

**In `knowledge/`, at the root of the repository**, one file per crop:
`knowledge/wheat.toml`.

§17 says agronomic values live in `data/`, and `0008` expected a crop
vocabulary there. But `.gitignore` excludes `data/*`, deliberately: that
folder is for farmers' real data and for large downloaded sets such as
CY-Bench, which never go to GitHub. The knowledge pack has to go there,
so the two rules collide. Each folder now keeps one rule: `src/` is
logic, `data/` is never committed, `knowledge/` always is. **§17's rule
is amended accordingly: agronomic values live in `knowledge/`, with a
citation per row and a test, or they do not exist.**

Rejected: an exception in `.gitignore`, such as `!data/knowledge/`. It
is a drawer labelled "never take out of the house" that also holds what
must be taken. Sooner or later the wrong thing goes out — a real CSV
dropped into the wrong subfolder becomes public, in a project that §11
says never commits real data, test fixtures included.

**TOML**, the format of `pyproject.toml`. It is read by `tomllib`, in
the standard library, so the pack adds no dependency; it allows
comments, which is where sources and warnings go; and it is already
familiar from this project.

Rejected:

- **JSON** — no comments.
- **YAML** — a new dependency, and it guesses the type of an unquoted
  value.
- **CSV** — good for one table, but a pack holds three kinds of thing
  (causes, questions, and what each answer rules out), so three files
  per crop. And Excel saves UTF-8 CSV with a byte-order mark, the one
  removed on 28 September.

**The shape.** Causes, each with an `id` and a `name`; questions, each
with an `id`, a `text`, and for every answer it accepts, the causes that
answer eliminates:

```toml
# Wheat, leaf yellowing.
# ILLUSTRATION, NOT KNOWLEDGE: no rule here has a source yet.

[[causes]]
id = "nitrogen_deficiency"
name = "nedostatak azota"

[[causes]]
id = "sulfur_deficiency"
name = "nedostatak sumpora"

[[questions]]
id = "leaf_age"
text = "Žute li prvo stariji (donji) listovi ili mlađi (gornji)?"

[questions.eliminates]
donji = ["sulfur_deficiency"]
gornji = ["nitrogen_deficiency"]
```

Identifiers and comments are English, because code and programmers read
them. Names, question text and answer words are Serbian, because a
farmer reads them, and an answer word is literally what the farmer types
(§15). The answers a question accepts are the keys of its `eliminates`
table, so an answer that rules nothing out is still listed, with an
empty list. One place says which answers exist, not two that could
disagree.

**An answer lists the causes it eliminates, not the causes it keeps.**
The picture is the game *Pogodi ko je?*. After each answer you knock
down the faces that do not match, and the ones you do not touch stay
standing. Forget to knock one down and the game takes one more
question. Under the opposite rule — knock everything down and raise
only the faces that match — a forgotten face stays down, and it may be
the right one.

The pack works the same way. A line forgotten under "eliminates"
weakens the narrowing. A line forgotten under "keeps" silently removes a
cause, possibly the true one, and the system names the wrong cause with
confidence. That is the more expensive error of the two: §8 prices a
missed cause at a field and a false alarm at one spray. **Silence means
the answer says nothing about that cause.**

**No sources yet, and the pack says so.** "Older leaves first rules out
sulfur" is agronomy, and §17 says agronomy without a source does not
exist. The skeleton's content is invented on purpose, to give the loop
something to run on, and none of it has a source. The picture is an
architect's cardboard model: it carries no specification for its
concrete, because its walls are not concrete, but it is plainly
labelled a model so that nobody mistakes it for the house. So the
skeleton's pack has no source field, and says it is an illustration in
its header, in the README, and in one line the CLI prints when a
conversation starts.

Rejected: a source field holding "none" or "illustration". One field
with two meanings, a citation or the absence of one — the sentinel §2
warns about.

## Consequences
**Adding a crop is adding a file**, and the claim in §4 becomes
something a commit can show.

**The pack is checked when it is read.** An answer that names a cause
the pack does not define is an error at startup, not a cause that is
silently never eliminated. A test loads the real file, so a broken pack
fails the suite.

**A bare TOML key is ASCII only.** An answer word with a diacritic has
to be quoted: `"mlađi" = [...]`. Unquoted, `tomllib` reports
`Expected '=' after a key in a key/value pair` at the column of the
diacritic, which points at the wrong problem. Measured with Python 3.13
on 21 October.

**`knowledge/` sits outside `src/`, so it is not part of the installed
package.** Run from the repository — `uv run fito`, the tests — that
changes nothing. Whatever ships the system has to ship the folder with
it: the Docker image at checkpoint 9.

**Whatever replaces elimination in checkpoint 2 has to read silence the
same way.** When answers start moving probabilities instead of knocking
causes down, a cause an answer does not mention is still one it says
nothing about.

**Revisit triggers:**
- **The real table, at checkpoint 2.** The source field arrives with
  it, required, so the rule arrives with the content it governs.
  Whether a source belongs to a question or to each elimination is
  decided against the real literature, not here.
- **A table an agronomist edits in a spreadsheet**, or one too large to
  read as TOML. CSV comes back into the argument then, BOM and all.
- **The first time the code runs from an installed package** rather
  than from the repository. The pack then moves under the package, or
  ships as data beside it.
- **A second symptom for the same crop.** One file per crop may become
  one file per crop and symptom.
