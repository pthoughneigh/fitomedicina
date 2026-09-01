"""Tests for ``Planting``'s lifecycle validator: status against the two dates.

Two rules are enforced and everything else is deliberately permitted, so most
of this file asserts that something is *accepted*. A stand may be established
with no record of when it went in, and terminated with no record of either
date. A schema that demanded those dates would be given invented ones, which
are indistinguishable from recorded ones and are read downstream as growing
degree days. The permissive tests exist to stop that tightening, and they fail
on the construction call rather than on an assertion.

Nothing here tests a transition between statuses. Status is a snapshot: a stand
entered retroactively arrives already ``TERMINATED`` and never existed in any
earlier state. A validator sees one object and has no previous value to compare
against, so a transition rule could only be approximated by demanding dates,
which is the same tightening under another name.

Both rules raise ``ValueError`` from the same validator, so both surface as
``type="value_error"`` with an empty ``loc``. The message is the only thing that
separates them, which is why the two negative tests assert on it.
"""

import uuid
from datetime import date

import pytest
from pydantic import ValidationError

from fito.schema.planting import Crop, EstablishmentMethod, Planting, PlantingStatus

FIELD_ID = uuid.uuid4()


def test_planned_with_establishment_date_raises() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Planting(
            field_id=FIELD_ID,
            status=PlantingStatus.PLANNED,
            crop=Crop.WHEAT,
            establishment_method=EstablishmentMethod.DIRECT_SOWN,
            establishment_date=date(2026, 8, 29),
        )

    errors = excinfo.value.errors()
    assert len(errors) == 1
    assert errors[0]["type"] == "value_error"
    assert errors[0]["loc"] == ()
    assert "A planned planting has no establishment date." in errors[0]["msg"]


def test_planned_without_establishment_date_passes() -> None:
    planting = Planting(
        field_id=FIELD_ID,
        status=PlantingStatus.PLANNED,
        crop=Crop.WHEAT,
        establishment_method=EstablishmentMethod.DIRECT_SOWN,
    )

    assert planting.establishment_date is None


def test_established_without_dates_passes() -> None:
    planting = Planting(
        field_id=FIELD_ID,
        status=PlantingStatus.ESTABLISHED,
        crop=Crop.WHEAT,
        establishment_method=EstablishmentMethod.DIRECT_SOWN,
    )

    assert planting.termination_date is None
    assert planting.establishment_date is None


def test_standing_crop_has_no_termination_date_passes() -> None:
    planting = Planting(
        field_id=FIELD_ID,
        status=PlantingStatus.ESTABLISHED,
        crop=Crop.WHEAT,
        establishment_method=EstablishmentMethod.DIRECT_SOWN,
        establishment_date=date(2026, 8, 29),
    )

    assert planting.establishment_date == date(2026, 8, 29)
    assert planting.termination_date is None


def test_terminated_without_any_dates_passes() -> None:
    planting = Planting(
        field_id=FIELD_ID,
        status=PlantingStatus.TERMINATED,
        crop=Crop.WHEAT,
        establishment_method=EstablishmentMethod.DIRECT_SOWN,
    )

    assert planting.establishment_date is None
    assert planting.termination_date is None


def test_termination_date_without_establishment_date_passes() -> None:
    planting = Planting(
        field_id=FIELD_ID,
        status=PlantingStatus.TERMINATED,
        crop=Crop.WHEAT,
        establishment_method=EstablishmentMethod.DIRECT_SOWN,
        termination_date=date(2026, 8, 29),
    )

    assert planting.establishment_date is None
    assert planting.termination_date == date(2026, 8, 29)


def test_termination_date_before_establishment_date_raises() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Planting(
            field_id=FIELD_ID,
            status=PlantingStatus.TERMINATED,
            crop=Crop.WHEAT,
            establishment_method=EstablishmentMethod.DIRECT_SOWN,
            termination_date=date(2026, 8, 29),
            establishment_date=date(2026, 9, 28),
        )

    errors = excinfo.value.errors()
    assert len(errors) == 1
    assert errors[0]["type"] == "value_error"
    assert errors[0]["loc"] == ()
    assert "Termination date cannot be before the establishment date." in errors[0]["msg"]
