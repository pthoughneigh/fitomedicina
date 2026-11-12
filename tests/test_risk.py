"""Tests for the risk worker's contract.

One test for each clause of the contract in ``assess_risk``'s docstring:
a probability for every cause in the pack and for nothing else, each
above zero, summing to one. The tests are meant to outlive the skeleton.
When weather replaces the level shares at checkpoint 3, the call gains
whatever the real worker needs, and the assertions stay as they are. That
the shares are level is not tested: it is the skeleton's flesh, and its
test would go with it.

The pack is written here, as in ``test_narrowing.py``, with abstract ids,
and with names that differ from the ids, so that a prior keyed by name
fails the first test. It has no questions, since the risk worker reads
only the causes.

The keys are compared as a set, because the contract promises which
causes, not in what order, and because pytest names the extra and the
missing items of two sets, where it does not for ``prior.keys()``.

The sum is compared with ``pytest.approx``, not with ``==``. Each share
of a correct prior is cut off in its last digit, and the cut-offs add
up: weights of 1, 1, 1.4 and 1, each divided by their total, sum to
0.9999999999999999 (measured). A test written with ``==`` would pass on
the level shares and fail on a real worker that does nothing wrong. The
default tolerance, one part in a million, sits far above that error and
far below a real one: a prior missing one of four causes sums to 0.75.
"""

import tomllib

import pytest

from fito.knowledge import KnowledgePack
from fito.workers.risk import assess_risk

PACK = KnowledgePack.model_validate(
    tomllib.loads("""
    illustrative = true
    questions = []

    [[causes]]
    id = "a"
    name = "uzrok a"

    [[causes]]
    id = "b"
    name = "uzrok b"

    [[causes]]
    id = "c"
    name = "uzrok c"

    """)
)


def test_prior_has_every_cause_and_nothing_else() -> None:
    prior = assess_risk(PACK).data
    assert set(prior.keys()) == {"a", "b", "c"}


def test_every_cause_starts_above_zero() -> None:
    prior = assess_risk(PACK).data
    assert min(prior.values()) > 0


def test_prior_sums_to_one() -> None:
    prior = assess_risk(PACK).data
    assert sum(prior.values()) == pytest.approx(1)
