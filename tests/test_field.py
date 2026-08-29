"""Tests for ``Field``'s coordinate validator and the ``grid_cell`` it derives."""

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
