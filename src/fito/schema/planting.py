"""The planting model and the controlled vocabularies it uses."""

import uuid
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic import Field as PydanticField


class Crop(str, Enum):
    """Crop species of a planting. Selects the knowledge pack for diagnosis."""

    WHEAT = "wheat"
    PEPPER = "pepper"


class Protection(str, Enum):
    """Physical structure over the planting.

    Load-bearing rather than descriptive: leaf wetness under plastic is not
    leaf wetness in the open, so this feeds the risk worker's disease priors.
    """

    OPEN = "open"
    TUNNEL = "tunnel"
    GREENHOUSE = "greenhouse"
    HAIL_NET = "hail_net"
    SHADE_NET = "shade_net"


class EstablishmentMethod(str, Enum):
    """How the stand was established, and therefore what its date means.

    Present so that ``establishment_date`` can be one column instead of
    ``sowing_date`` and ``transplant_date``, exactly one of which is always null.
    """

    DIRECT_SOWN = "direct_sown"
    TRANSPLANTED = "transplanted"
    PLANTED_STOCK = "planted_stock"


class PlantingStatus(str, Enum):
    """Lifecycle stage of the stand.

    ``PLANNED`` covers ground committed to a crop but not yet in it, which is
    what makes a null establishment date legitimate rather than missing data.
    """

    PLANNED = "planned"
    ESTABLISHED = "established"
    TERMINATED = "terminated"


class Planting(BaseModel):
    """A stand of one crop, established on a date, occupying part or all of a field.

    Not a season. The orchard was planted in 2016 and will still be there in
    2036, while a smallholder can have two stands in the ground at once and a
    third already finished. A season is a filter over these, not a thing to
    store.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        validate_assignment=True,
    )

    id: uuid.UUID = PydanticField(default_factory=uuid.uuid4)
    field_id: uuid.UUID
    crop: Crop
    status: PlantingStatus
    establishment_method: EstablishmentMethod
    variety: str | None = None
    rootstock: str | None = None
    area_ha: Decimal | None = PydanticField(default=None, gt=0, max_digits=10, decimal_places=4)
    location_note: str | None = None
    protection: Protection = Protection.OPEN
    establishment_date: date | None = None
    termination_date: date | None = None
    plant_density: int | None = PydanticField(default=None, gt=0)
    seed_rate_kg_ha: Decimal | None = PydanticField(default=None, gt=0, decimal_places=4)
    preceding_crop: Crop | None = None

    @model_validator(mode="after")
    def _check_lifecycle_consistency(self) -> Self:
        """Reject a status and a date pair that contradict each other.

        A ``PLANNED`` stand is ground committed to a crop but not yet in it, so
        an establishment date on one is not late data but a claim that argues
        with itself. The reverse is allowed: ``ESTABLISHED`` and ``TERMINATED``
        without a date are incomplete rather than wrong, and a farmer who knows
        the wheat is standing but not whether it went in on 12 or 15 October
        should not be made to invent one.

        The two dates are independent, unlike the coordinate pair on ``Field``.
        Wheat sown in October has no termination date until July; the orchard
        will have none for twenty years; a crop entered retroactively can have a
        termination date and no establishment date. All four combinations are
        legitimate. Only their order is constrained, and only when both exist.

        The comparison is >, not >=, so both dates falling on one day is accepted
        rather than rejected. A stand hailed out on the afternoon it was sown, or
        one sown to the wrong crop and ploughed back in the same day, is short but
        not impossible.

        Status is a snapshot, not a step in a sequence. A stand may enter the
        system in any of the three states, so nothing here may test a
        transition — there is often no previous state to have come from.
        """

        if (self.status == PlantingStatus.PLANNED) and (self.establishment_date is not None):
            raise ValueError("A planned planting has no establishment date.")
        if (
            (self.establishment_date is not None)
            and (self.termination_date is not None)
            and (self.establishment_date > self.termination_date)
        ):
            raise ValueError("Termination date cannot be before the establishment date.")
        return self
