"""The ``fields`` table: the stored shape of a field.

Deliberately a separate class from ``fito.schema.field.Field``. The validated
model and the stored row are allowed to diverge -- the pseudonymised payload
that leaves the country is not the row that stays behind -- and one file per
layer keeps that divergence visible instead of looking like duplication.
"""

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from fito.db.base import Base
from fito.schema.field import Country, Drainage, Irrigation, Slope, SoilTexture, SoilType


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


class CadastralParcelRow(Base):
    __tablename__ = "cadastral_parcels"

    field_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("fields.id"), primary_key=True)
    parcel_number: Mapped[str] = mapped_column(primary_key=True)
