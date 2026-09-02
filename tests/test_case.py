"""Tests for ``Case``'s field constraints. There are no cross-field rules to test.

``Case`` has no ``model_validator``, so nothing here looks like the lifecycle
tests on ``Planting``. Errors carry the attribute name in ``loc`` rather than an
empty one, because every rule these tests exercise belongs to a single field.

Two of the three guard values that vanish silently. ``min_length=1`` is what
separates a required message from an accepted one made of spaces, since
``str_strip_whitespace`` empties the string but does not reject it. And
``datetime.now(UTC)`` differs from ``datetime.now`` by an offset that is never
recorded and cannot be recovered afterwards -- the swap is one word long, breaks
nothing visibly, and decisions/0006 rests on it not happening.

The third asserts that ``observed_on`` defaults to ``None``. No plausible edit
makes it fail; it is here because a farmer knowing "last week" but not the day
is a decision, and this is where it is legible without opening decisions/.
"""

import uuid
from datetime import UTC

import pytest
from pydantic import ValidationError

from fito.schema.case import Case

PLANTING_ID = uuid.uuid4()


def test_initial_message_with_only_spaces_raises() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Case(planting_id=PLANTING_ID, initial_message="     ")

    errors = excinfo.value.errors()
    assert len(errors) == 1
    assert errors[0]["type"] == "string_too_short"
    assert errors[0]["loc"] == ("initial_message",)


def test_opened_at_is_timezone_aware_passes() -> None:
    case = Case(
        planting_id=PLANTING_ID,
        initial_message="Something went wrong with the wheat....",
    )

    assert case.opened_at.tzinfo == UTC


def test_observed_on_default_is_none_passes() -> None:
    case = Case(
        planting_id=PLANTING_ID,
        initial_message="Something went wrong with the wheat....",
    )

    assert case.observed_on is None
