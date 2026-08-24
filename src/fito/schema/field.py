"""Controlled vocabularies for the agronomic parcel model.

Members subclass ``str``, so ``Country.RS == "RS"`` holds and ``json.dumps``
serialises them as their value.

Gotcha: on Python 3.11+ an f-string goes through ``Enum.__format__`` and
renders ``"Country.RS"``, while concatenation goes through ``str`` and renders
``"RS"``. Same object, two results. Use ``.value`` for any text that leaves the
process -- prompts, logs, URLs, filenames.
"""

from enum import Enum


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
    """Ordinal slope class of the parcel.

    Gradient breakpoints are not fixed yet -- until they are, the classes are
    only ordered labels. See notes/agronomy_raw.md.
    """

    FLAT = "flat"
    GENTLE = "gentle"
    MODERATE = "moderate"
    STEEP = "steep"


class Irrigation(str, Enum):
    """Irrigation system installed on the parcel."""

    # Surveyed fact: no system, parcel is rain-fed. Distinct from a missing
    # field (Python None), which means nobody has recorded it yet.
    NONE = "none"
    DRIP = "drip"
    SPRINKLER = "sprinkler"
    PIVOT = "pivot"
    FURROW = "furrow"


class Drainage(str, Enum):
    """Artificial drainage installed on the parcel."""

    # Surveyed fact: no artificial drainage. Distinct from a missing field
    # (Python None), which means nobody has recorded it yet.
    NONE = "none"
    OPEN_CHANNEL = "open_channel"
    TILE = "tile"
