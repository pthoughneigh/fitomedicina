"""Controlled vocabularies for the agronomic field model.

Members subclass ``str``, so ``Country.RS == "RS"`` holds and ``json.dumps``
serialises them as their value.

Gotcha: on Python 3.11+ an f-string goes through ``Enum.__format__`` and
renders ``"Country.RS"``, while concatenation goes through ``str`` and renders
``"RS"``. Same object, two results. Use ``.value`` for any text that leaves the
process -- prompts, logs, URLs, filenames.
"""

import uuid
from decimal import ROUND_FLOOR, Decimal
from enum import Enum
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic import Field as PydanticField

# 1.1 km
# Quantisation step for ``Field.grid_cell``. At 45 deg N, 0.01 deg spans about
# 1113 m of latitude and about 790 m of longitude, so a cell is roughly 90 ha.
GRID_CELL_DEGREES = Decimal("0.01")


class Country(str, Enum):
    """ISO 3166-1 alpha-2 country code, restricted to the modelled region."""

    RS = "RS"
    HR = "HR"
    BA = "BA"
    ME = "ME"


class SoilType(str, Enum):
    """WRB Reference Soil Group. Read off a soil map, not measured in field."""

    CHERNOZEM = "chernozem"
    FLUVISOL = "fluvisol"
    GLEYSOL = "gleysol"
    VERTISOL = "vertisol"
    CAMBISOL = "cambisol"


class SoilTexture(str, Enum):
    """USDA textural class of the topsoil (0-30 cm), fine earth < 2 mm."""

    SANDY_LOAM = "sandy_loam"
    CLAY_LOAM = "clay_loam"
    SILTY_CLAY_LOAM = "silty_clay_loam"
    LOAM = "loam"
    SANDY_CLAY_LOAM = "sandy_clay_loam"
    SILT_LOAM = "silt_loam"
    CLAY = "clay"
    SAND = "sand"


class Slope(str, Enum):
    """Ordinal slope class of the field.

    Gradient breakpoints are not fixed yet -- until they are, the classes are
    only ordered labels.
    """

    FLAT = "flat"
    GENTLE = "gentle"
    MODERATE = "moderate"
    STEEP = "steep"


class Irrigation(str, Enum):
    """Irrigation system installed on the field."""

    # Surveyed fact: no system, field is rain-fed.
    # Not nullable, unlike `drainage`: rain-fed is the regional default, so an
    # unrecorded field is assumed rain-fed. See decisions/0004.
    NONE = "none"
    DRIP = "drip"
    SPRINKLER = "sprinkler"
    PIVOT = "pivot"
    FURROW = "furrow"


class Drainage(str, Enum):
    """Artificial drainage installed on the field."""

    # Surveyed fact: no artificial drainage. Distinct from an unset value
    # (Python None), which means nobody has recorded it yet.
    NONE = "none"
    OPEN_CHANNEL = "open_channel"
    TILE = "tile"


class Field(BaseModel):
    """A durable unit of land management: one contiguous area worked as a whole.

    Distinct from a cadastral parcel, which is a legal record and may be
    several per field, and from a crop, which changes season to season while
    the field persists.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        validate_assignment=True,
    )

    id: uuid.UUID = PydanticField(default_factory=uuid.uuid4)
    country: Country
    holding_id: uuid.UUID | None = None
    name: str | None = None
    latitude: Decimal | None = PydanticField(default=None, ge=-90, le=90, decimal_places=6)
    longitude: Decimal | None = PydanticField(default=None, ge=-180, le=180, decimal_places=6)
    grid_cell: str | None = None
    municipality: str | None = None
    cadastral_parcels: list[str] = PydanticField(default_factory=list)
    cadastral_municipality: str | None = None
    area_ha: Decimal | None = PydanticField(default=None, gt=0, max_digits=10, decimal_places=4)
    soil_type: SoilType | None = None
    soil_texture: SoilTexture | None = None
    slope: Slope | None = None
    irrigation: Irrigation = Irrigation.NONE
    drainage: Drainage | None = None

    @model_validator(mode="after")
    def _check_coordinates_and_derive_grid_cell(self) -> Self:
        """Reject a half-set coordinate pair, then derive ``grid_cell`` from it.

        One coordinate without the other is not partial data but wrong data:
        downstream code that coalesces the missing half to zero puts the field in
        the Gulf of Guinea instead of failing, and a plausible-looking point is
        much harder to notice than a null one.

        ``grid_cell`` is the coarsened location, and the only spatial value that
        may leave the country: both coordinates truncated to
        ``GRID_CELL_DEGREES`` and joined as ``"45.87,19.35"``. Truncation is
        ``ROUND_FLOOR``, not ``ROUND_DOWN``, so the tiling stays uniform across
        the meridian and the equator rather than doubling the width of the cells
        that straddle zero.

        The value is therefore the **south-west corner of the cell, not a point
        within it**. Plotting it as a point shifts every field half a cell south
        and west; add half a cell first if an approximate centre is wanted.

        Derived on every validation pass, so any ``grid_cell`` supplied by the
        caller is overwritten rather than rejected. That keeps
        ``Field(**old.model_dump())`` working, and a supplied value could only
        ever disagree with the coordinates it claims to summarise.

        Runs in ``mode="after"``, so both coordinates have already passed their
        own range checks and are ``Decimal`` or ``None`` by this point.

        Two consequences of ``validate_assignment=True``. This re-runs on every
        attribute set, so the coordinates cannot be filled in one at a time --
        assigning ``latitude`` alone raises. Rebuild instead, which re-validates:
        ``Field(**old.model_dump() | {"latitude": lat, "longitude": lon})``. Not
        ``model_copy(update=...)``, which writes straight to the instance and
        runs no validators at all. And ``grid_cell`` is written through
        ``__dict__`` below, because a plain assignment here would re-enter this
        validator without end.
        """
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Longitude and latitude must be given together.")

        # Written through __dict__ to bypass validate_assignment; see docstring.
        if self.latitude is None or self.longitude is None:
            self.__dict__["grid_cell"] = None
            return self

        self.__dict__["grid_cell"] = (
            f"{self.latitude.quantize(GRID_CELL_DEGREES, rounding=ROUND_FLOOR)},"
            f"{self.longitude.quantize(GRID_CELL_DEGREES, rounding=ROUND_FLOOR)}"
        )

        return self
