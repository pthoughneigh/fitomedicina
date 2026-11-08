# 0021 — The farmer app ships before the analytics mode

**Date:** 2026-11-08
**Status:** accepted

## Context
§1 describes two modes over one field profile: chat for a farmer, built
first, and analytics for a farm or company that uploads its history,
built second. §11's checkpoints keep that order to the end. Analytics is
checkpoint 8 and deployment is checkpoint 9, so nothing reaches a real
user until the half built for companies is finished too. §9 adds that a
real chat frontend becomes a decision only if real users arrive.

The goal is now a farmer app in production and in public use before any
work for companies begins. That leaves three things to settle: what
moves behind the launch and what stays ahead of it, what the launch
itself has to contain, and how the app reaches a phone. §14 puts the
farmer in a field, on a phone, with one hand, and the app is to run as
a website first and on phones and tablets later.

Dropping analytics altogether was weighed on 8 November. It would save
checkpoint 8, the import layer and probably the comparison worker — a
few months of a plan of twelve to eighteen — and lose the clearest
route to revenue (§13). Nothing built so far depends on that choice.

## Decision
**Checkpoint 9 comes before checkpoint 8.** The order is now 1 to 7,
then 9, then 8. The numbers stay as they are, because the records and
the context file cite them. They are addresses, not places in a queue:
building house number 9 before number 8 does not renumber the street.

**Behind the launch, with checkpoint 8:**

- **The named analyses**, their reports, and the Streamlit dashboard
  with its Plotly charts (§9).
- **The import layer**, taken out of checkpoint 5, and with it what
  `0002` and `0005` placed there: the alias tables and the check of a
  field's area against its plantings. Both records put them at
  checkpoint 5 because the import path was there, and they stay with
  the import path.
- **The comparison worker.** It reports what happened on fields like
  this one, and before the launch there are no others to compare with:
  no uploaded histories, and a season log that only real use fills. The
  unsupervised methods of §8 arrive with it.

**Ahead of the launch, everything that serves the farmer, unchanged:**
the real narrowing loop (2), live weather and soil (3), the first
trained model and its honest evaluation (4) — splits by year, ROC, a
confusion matrix priced by §8's asymmetry, the calibration curve —
persistence and the season log without the import layer (5), paprika
(6) and the evidence worker (7). This record takes nothing away from
the statistics of the farmer half. They are much of what it is made of.

**Checkpoint 9 grows from "deployed" to "launched".** FastAPI, Docker
and observability as before, and two things more:

- **A web frontend for the farmer, designed for a phone first.** It is
  a client, as the CLI is: it holds the state and passes it along
  (`0019`), and no rule lives in it. Its technology is chosen at
  checkpoint 9, against what is built by then.
- **The launch gate.** Nothing goes public before everything §5
  requires ahead of real users is in place, including the review by a
  lawyer qualified in Serbian data protection law. Two questions raised
  on 6 November, still open, close here as well: the sentence telling
  the farmer that the answer comes from software, not from an
  agronomist; and the conflict between §13's cap of about five
  conversations a month and the promise in `0017` not to track an
  anonymous visitor. A cap per person needs the person recognised, so
  one of the two gives way.

**Phones and tablets later, over the same API.** Every client is a thin
layer over one API: first a website that works in a phone's browser,
then the same site installable on the phone's home screen, then a
native app if one is ever needed. A tablet is a wider screen for the
same website. Nothing on the server changes for any of them. That is
what the shape in `0019` buys: each client hands over the state and one
message, and gets a reply and the new state back.

**The company half keeps its place by not being closed off, not by
being built ahead.** The schema is shared, as §1 intends, and it was
derived from four profiles, one of them a company's 214 ha block
(§16). Nothing built for the farmer may narrow it: a field already
exists without a holding (`holding_id` is optional) and will exist with
one. The parts only a company uses are built when a company is there to
use them, as every other part of this project is built when something
reads it.

Rejected:

- **Keeping §11's order.** The first real user would wait for a mode
  built for another kind of user, and the comparison worker would be
  built against data that does not exist yet.
- **Dropping analytics now.** A few months saved, and the clearest
  willingness to pay lost (§13), to settle a question that answers
  itself later: once the farmer app is live, it is known whether anyone
  asks for analysis. Deferring the choice costs nothing, because
  nothing built depends on it.
- **A web frontend before checkpoint 9.** §18's reasons for the CLI
  first still hold. The eval harness calls the supervisor, not HTTP,
  and keeping a conversation between messages is LangGraph's job, so a
  frontend built early hand-rolls that and throws it away.
- **A native app first.** Two app stores, two codebases or a
  cross-platform framework, and a store review between every fix and
  the farmer, for a product with no users yet. A website reaches every
  phone from the first day, and the API does not change when a native
  app arrives.

## Consequences
**§11's order and §9's sentence on the chat frontend are amended
accordingly**, and so is "built second" in §1, which now means after
the launch.

**`0002` and `0005` are due with the import layer, after the launch**,
no longer at checkpoint 5. What they decide does not change, only when
it arrives. One thing meant for the import layer is needed earlier.
§17 put the truncation of coordinates to six decimals there because "a
phone returning eight decimals fails validation", and now the phone
comes first. The truncation goes where a client's input enters, the API
at checkpoint 9 at the latest, and `decimal_places` stays the backstop.

**Until the import layer exists, nothing checks a field's area against
its plantings.** At the launch that is harmless: a conversation's own
field holds only its country (`0017`), and §14's screens for a farmer
take no area. If a farmer gets a way to enter one before the import
layer exists, the check comes with it.

**Checkpoint 9 becomes the largest checkpoint, and its slowest part is
outside the project.** A lawyer's review runs on someone else's
calendar, so it is requested while checkpoint 9 is being built, not
after its code is finished. Some of §5 arrives much earlier anyway: the
pseudonymization boundary with the model, EXIF stripping with the
first photo.

**Two farmer features still have no checkpoint**: treatment from the
registry (`0007`) and the triage of photos. Both are on the farmer's
side of the line this record draws, so neither waits for analytics.
Whether each is in the first public version is decided at checkpoint 9,
against what is built by then.

**A phone first applies to the design, not only to the stack.** §14's
screens — one input to start, one question at a time, the diagnosis
card and its "why" — are designed at a phone's width and widened for a
desktop, not designed for a desktop and squeezed.

**Revisit triggers:**
- **The farmer app is live.** Whether checkpoint 8 is built, cut or
  replaced by what users actually ask for is decided then, with real
  use to decide it on. This record defers that choice; it does not
  make it.
- **A company asks for analysis before the launch**, with its data and
  a question. A user ready to pay is a reason to change the order
  again.
- **Something a farmer needs that the website cannot do well on a
  phone**: working without signal in the field, say, or the season-log
  prompt of §14 arriving as a notification. A native client becomes a
  decision then, over the same API.
