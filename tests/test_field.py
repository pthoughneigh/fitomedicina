"""Tests for ``Field``'s validators: coordinates, ``grid_cell``, parcel order.

``grid_cell`` is the only spatial value permitted to leave the country, so the
tests that pin its formatting are pinning a privacy boundary rather than a
string. Two decimal places, zero-padded, floored rather than truncated: a swap
to ``ROUND_DOWN`` is invisible in the region being modelled and shows up only
below zero, which is why one test sits in the South Pacific.

``test_unknown_key_raises`` and ``test_rebuild_field_equals_original``
are not about coordinates. ``extra="forbid"`` and the rebuild idiom are
model configuration, and they are here because nothing else would notice
if they were dropped. They also record the other half of a distinction
the negative tests rely on: a field-level error carries the attribute name
in ``loc``, while a rule spanning several attributes carries an empty one.

``test_cadastral_parcels_are_kept_sorted_in_string_order`` holds the one
rule on parcels, and holds it here, without a database. The round-trip
test also fails when the model stops sorting, but only because SQLite
hands the parcels back sorted; a database returning them in the order
written would leave it green. The input is out of order in string terms,
and the expected value pins string order rather than numeric: ``1234/10``
before ``1234/9`` (decisions/0014).
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from fito.schema.field import Country, Field


def test_grid_cell_is_none_without_coordinates() -> None:
    field = Field(country=Country.RS)
    assert field.grid_cell is None


def test_grid_cell_derived_from_both_coordinates() -> None:
    field = Field(country=Country.RS, latitude=Decimal("45.8765"), longitude=Decimal("19.3512"))
    assert field.grid_cell == "45.87,19.35"


# Deliberately outside the region: ROUND_FLOOR and ROUND_DOWN agree above zero
# and differ below it, so only a negative pair can catch a swap between them.
def test_grid_cell_floors_negative_coordinates_downward() -> None:
    field = Field(country=Country.RS, latitude=Decimal("-45.7744"), longitude=Decimal("-160.888"))
    assert field.grid_cell == "-45.78,-160.89"


def test_grid_cell_pads_to_two_decimal_places() -> None:
    field = Field(country=Country.RS, latitude=Decimal("45.8"), longitude=Decimal("19.3"))
    assert field.grid_cell == "45.80,19.30"


def test_grid_cell_supplied_by_caller_is_overwritten() -> None:
    field = Field(
        country=Country.RS,
        latitude=Decimal("45.8765"),
        longitude=Decimal("19.3512"),
        grid_cell="garbage",
    )
    assert field.grid_cell == "45.87,19.35"


def test_half_set_coordinate_pair_raises() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Field(country=Country.RS, longitude=Decimal("-160.888"))

    errors = excinfo.value.errors()
    assert len(errors) == 1
    assert errors[0]["type"] == "value_error"
    assert errors[0]["loc"] == ()


def test_assigning_one_coordinate_raises() -> None:
    field = Field(country=Country.RS)
    with pytest.raises(ValidationError) as excinfo:
        field.latitude = Decimal("45.8")

    errors = excinfo.value.errors()
    assert len(errors) == 1
    assert errors[0]["type"] == "value_error"
    assert errors[0]["loc"] == ()


def test_unknown_key_raises() -> None:
    with pytest.raises(ValidationError) as excinfo:
        Field(country=Country.RS, unknown_variable=Decimal("19.35"))

    errors = excinfo.value.errors()
    assert len(errors) == 1
    assert errors[0]["type"] == "extra_forbidden"
    assert errors[0]["loc"] == ("unknown_variable",)


def test_rebuild_field_equals_original() -> None:
    original = Field(
        country=Country.RS,
        latitude=Decimal("45.8"),
        longitude=Decimal("19.3"),
        municipality="Backa",
        area_ha=Decimal("10"),
    )
    rebuilt = Field(**original.model_dump())
    assert rebuilt == original


def test_cadastral_parcels_are_kept_sorted_in_string_order() -> None:
    field = Field(country=Country.RS, cadastral_parcels=["1234/9", "1234/10"])
    assert field.cadastral_parcels == ["1234/10", "1234/9"]
