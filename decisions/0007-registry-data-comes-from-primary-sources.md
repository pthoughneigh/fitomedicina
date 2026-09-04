# 0007 — Registry data comes from primary sources
**Date:** 2026-09-03
**Status:** accepted

## Context
The system will eventually name a product and a pre-harvest interval. Both
are legal facts, not agronomic opinions: an interval that is wrong by a week
sends residue to market, and a product not registered for a crop is an
offence to recommend.

Two routes to that data exist.

`pesticidi.org` (AgroVodič) aggregates it and is far easier to read. One page
per product carries crop, dose, water volume, timing, pre-harvest interval,
FRAC/IRAC/HRAC group and registration validity, all in one shape.

The official chain has three links and no single page: the Plant Protection
Directorate publishes a list of registered products with a decision number
and an expiry date but no crop, dose or interval; the decision number appears
again on the manufacturer's label; the label carries everything else.

The aggregator is not the official chain. Its own footer disclaims accuracy
and directs the reader to the label before use, and two failures were
observed on a single afternoon of reading it:

- **Vitra** — the page gives dose, water volume, timing and a 28-day interval,
  and omits the maximum number of treatments. The label states two per season.
  A system reasoning from the page would recommend a third.
- **Acramite 480 SC** — a dose is listed against paprika, footnoted in smaller
  type as pending registration. Read mechanically, that is a dose for a crop
  the product is not registered for.

Both are the same failure: a field silently absent or silently qualified,
where absence reads as permission.

The aggregator's terms of use settle this independently of data quality.
Copyright is claimed over the site's content and its **databases** by name,
not only its prose, and the permission granted to a visitor is to use that
content for personal purposes at their own risk. Retrieving it
systematically to populate this project is neither personal nor covered,
whatever the origin of the individual facts. Reading the site to learn which
products exist for a crop remains ordinary use of it as a visitor; that is
the whole of the discovery step above.

## Decision
Aggregators are used for **discovery** — which products exist for a crop,
what to go and look up. Never as the source of a number that reaches a user.

Every number comes from the primary document: the Directorate's list for
whether a registration is valid and until when, the manufacturer's label for
crop, dose, timing, pre-harvest interval, re-entry interval, maximum
treatments and tank-mix restrictions. The decision number joins the two.

Three consequences of that, which are part of this decision rather than
implementation detail:

The original PDF is stored, not only the values extracted from it. When a
number is questioned a year from now, the answer is the document, not this
project's table of it.

Every stored document records where it came from and when it was retrieved.
A registry is a statement about a date — the Directorate's own list says
which decisions it covers — so a value without a retrieval date cannot be
told from a current one.

A changed label is an event to be surfaced, never overwritten in place. The
change may be the interval, and a silent update is indistinguishable from
having been wrong all along.

## Consequences
This is slower. The aggregator is one page per product; the chain is a list
lookup plus a label, and labels sit on manufacturers' own sites in no common
location.

Only the crop being modelled needs doing. Paprika is a few dozen products
once herbicides, insecticides and expired registrations are excluded, and
fewer active substances than products — trade names multiply where chemistry
does not.

Nothing here is built. The record exists because the shortcut becomes
tempting exactly when the work is due, and because both failures above are
invisible in the aggregated data itself: they are only visible against the
label.

Two independent reasons now point the same way, which is worth noting
because they could have conflicted: the primary documents are both the
accurate route and the unencumbered one. Had the aggregator been more
accurate, this decision would have been a harder one and would have been a
question for a lawyer rather than a design record.

**Revisit trigger:** the Directorate publishing its list in a machine-readable
form, or any official database indexed by crop. Either shortens the chain and
this record is then about a route that no longer exists.
