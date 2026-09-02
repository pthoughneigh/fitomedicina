"""The case model: a problem a farmer reported, at the moment they reported it."""

import uuid
from datetime import UTC, date, datetime

from pydantic import BaseModel, ConfigDict
from pydantic import Field as PydanticField


class Case(BaseModel):
    """One reported problem on one stand.

    Unlike ``Field`` and ``Planting``, which describe things that exist whether
    or not anyone asks about them, a case exists because someone asked. It is a
    record of an interaction, and its content is what a person wrote rather than
    what the system concluded.

    The reference is to a planting, not a field. A planting already carries its
    ``field_id``, so a case reaches the soil, the slope and the ``grid_cell``
    through it, while the reverse would not reach the crop -- and the crop
    selects the knowledge pack without which there is no differential diagnosis.

    No ``model_validator``. A symptom is always seen before it is reported, so
    ``observed_on`` after ``opened_at`` is an error, but the two are different
    kinds of time and comparing them needs a timezone this model has no route
    to. The absence is the decision; see decisions/0006 before adding the
    one-line comparison it looks like it is missing.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        validate_assignment=True,
    )

    # Stays v4 even if other entities move to v7. This id can appear in a URL,
    # and a v7 timestamp beside `grid_cell` would disclose that someone within a
    # 1.1 km cell had a problem at a known moment -- which is what `grid_cell`
    # exists to prevent. See decisions/0003.
    id: uuid.UUID = PydanticField(default_factory=uuid.uuid4)
    planting_id: uuid.UUID
    # The farmer's own words, kept verbatim and kept permanently. A later
    # symptom vocabulary will read this rather than replace it: the text is the
    # datum, anything extracted from it is an interpretation, and a system that
    # reports honest confidence has to be able to tell the two apart.
    # `initial_` because a diagnosis is a conversation; later exchanges are a
    # separate model, not more of this field.
    initial_message: str = PydanticField(min_length=1)
    # Nullable: a farmer knows it was "last week" more reliably than a date, and
    # a required field would be answered with an invented one.
    observed_on: date | None = None
    # Timezone-aware and UTC, not `datetime.now`, whose offset is the machine's
    # and is lost unrecoverably. See decisions/0006.
    opened_at: datetime = PydanticField(default_factory=lambda: datetime.now(UTC))
