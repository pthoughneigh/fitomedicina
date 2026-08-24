from enum import Enum


class Country(str, Enum):
    RS = "RS"
    HR = "HR"
    BA = "BA"
    ME = "ME"


class SoilType(str, Enum):
    CHERNOZEM = "chernozem"
    FLUVISOL = "fluvisol"
    GLEYSOL = "gleysol"
    VERTISOL = "vertisol"
    CAMBISOL = "cambisol"


class SoilTexture(str, Enum):
    SANDY_LOAM = "sandy_loam"
    CLAY_LOAM = "clay_loam"
    SILTY_CLAY_LOAM = "silty_clay_loam"
    LOAM = "loam"
    SANDY_CLAY_LOAM = "sandy_clay_loam"
    SILT_LOAM = "silt_loam"
    CLAY = "clay"
    SAND = "sand"


class Slope(str, Enum):
    FLAT = "flat"
    GENTLE = "gentle"
    MODERATE = "moderate"
    STEEP = "steep"


class Irrigation(str, Enum):
    NONE = "none"
    DRIP = "drip"
    SPRINKLER = "sprinkler"
    PIVOT = "pivot"
    FURROW = "furrow"


class Drainage(str, Enum):
    NONE = "none"
    OPEN_CHANNEL = "open_channel"
    TILE = "tile"
