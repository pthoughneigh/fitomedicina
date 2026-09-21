"""The ``fields`` table: the stored shape of a field.

Deliberately a separate class from ``fito.schema.field.Field``. The validated
model and the stored row are allowed to diverge -- the pseudonymised payload
that leaves the country is not the row that stays behind -- and one file per
layer keeps that divergence visible instead of looking like duplication.
"""

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fito.db.base import Base
from fito.schema.field import Country, Drainage, Field, Irrigation, Slope, SoilTexture, SoilType


class FieldRow(Base):
    """One row in ``fields``.

    Validation lives in ``fito.schema.field.Field``, not here. This class
    stores what it is handed: no range is re-checked, no vocabulary is
    enforced, no coordinate pair is re-validated at this layer.
    """

    __tablename__ = "fields"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)

    # No ForeignKey: ``holdings`` has no table yet, and a reference into a
    # registry that does not contain the target fails to resolve. The column
    # carries the value; it gains the constraint when the table lands.
    holding_id: Mapped[uuid.UUID | None] = mapped_column()
    country: Mapped[Country] = mapped_column()

    name: Mapped[str | None] = mapped_column()
    grid_cell: Mapped[str | None] = mapped_column()
    municipality: Mapped[str | None] = mapped_column()
    cadastral_municipality: Mapped[str | None] = mapped_column()
    soil_type: Mapped[SoilType | None] = mapped_column()
    soil_texture: Mapped[SoilTexture | None] = mapped_column()
    slope: Mapped[Slope | None] = mapped_column()
    irrigation: Mapped[Irrigation] = mapped_column()
    drainage: Mapped[Drainage | None] = mapped_column()

    latitude: Mapped[Decimal | None] = mapped_column()
    longitude: Mapped[Decimal | None] = mapped_column()
    area_ha: Mapped[Decimal | None] = mapped_column()

    # Not a column. ``ForeignKey`` tells the database the two are related;
    # this tells the ORM. Without it the ORM writes rows in the order they
    # were added, and a parcel written before its field fails the constraint
    # -- which is now visible, because the pragma is on.
    #
    # ``delete-orphan`` rather than the default, which blanks the child's
    # foreign key and leaves it. ``field_id`` is half the primary key, so it
    # cannot be blanked, and an erasure request has to take the parcels with
    # the field rather than orphan them.
    #
    # One direction only. Nothing reads from a parcel up towards its field,
    # and the reverse side costs one line in each class on the day it does.
    # Two relationships over one foreign key must name each other through
    # ``back_populates`` or SQLAlchemy warns that they will disagree.
    cadastral_parcels: Mapped[list["CadastralParcelRow"]] = relationship(
        cascade="all, delete-orphan"
    )


class CadastralParcelRow(Base):
    __tablename__ = "cadastral_parcels"

    field_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("fields.id"), primary_key=True)
    parcel_number: Mapped[str] = mapped_column(primary_key=True)


def to_field_row(field: Field) -> FieldRow:
    """Build the row for ``field``, with its cadastral parcels attached.

    Field by field rather than ``FieldRow(**field.model_dump())``: that line
    holds only while the two shapes match, and the module docstring already
    says they will not.

    Parcels are built from ``parcel_number`` alone. ``field_id`` is left
    unset on purpose: the relationship writes it at flush, from the field the
    parcel is attached to. Half of the parcel's primary key is missing here
    and that is correct.
    """
    return FieldRow(
        id=field.id,
        country=field.country,
        holding_id=field.holding_id,
        name=field.name,
        grid_cell=field.grid_cell,
        municipality=field.municipality,
        cadastral_municipality=field.cadastral_municipality,
        soil_type=field.soil_type,
        soil_texture=field.soil_texture,
        slope=field.slope,
        irrigation=field.irrigation,
        drainage=field.drainage,
        latitude=field.latitude,
        longitude=field.longitude,
        area_ha=field.area_ha,
        cadastral_parcels=[
            CadastralParcelRow(parcel_number=parcel_number)
            for parcel_number in field.cadastral_parcels
        ],
    )
