"""The ``plantings`` table: the stored shape of a planting.

A separate class from ``fito.schema.planting.Planting``, for the reason
``fito.db.field`` gives: the validated model and the stored row are
allowed to diverge, and one file per layer keeps that visible.
"""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from fito.db.base import Base
from fito.schema.planting import Crop, EstablishmentMethod, Planting, PlantingStatus, Protection


class PlantingRow(Base):
    """One row in ``plantings``.

    Validation lives in ``fito.schema.planting.Planting``, not here. This
    class stores what it is handed: no vocabulary is enforced and neither
    lifecycle rule is re-checked at this layer. No column has a default
    either, ``protection`` included: the model mints values and the row
    carries them.
    """

    __tablename__ = "plantings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    # Deleting a field deletes its plantings in the database itself, through
    # ``ON DELETE CASCADE``, whoever deletes the field: the ORM, or a bulk
    # ``delete`` that bypasses it. SQLite honours it only on connections with
    # foreign keys on, which ``build_engine`` sets; without them the field
    # goes and its plantings stay behind, silently. No ``relationship`` from
    # ``FieldRow``, unlike the parcels: nothing writes or reads plantings
    # through their field. decisions/0016.
    field_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("fields.id", ondelete="CASCADE"))
    crop: Mapped[Crop] = mapped_column()
    # Nullable since decisions/0017, following the model: an anonymous
    # planting is stored with neither. The ``| None`` is what removes
    # ``NOT NULL`` from the DDL; without it the model accepts the planting
    # and the database refuses it on commit.
    status: Mapped[PlantingStatus | None] = mapped_column()
    establishment_method: Mapped[EstablishmentMethod | None] = mapped_column()
    variety: Mapped[str | None] = mapped_column()
    rootstock: Mapped[str | None] = mapped_column()
    area_ha: Mapped[Decimal | None] = mapped_column()
    location_note: Mapped[str | None] = mapped_column()
    protection: Mapped[Protection] = mapped_column()
    establishment_date: Mapped[date | None] = mapped_column()
    termination_date: Mapped[date | None] = mapped_column()
    plant_density: Mapped[int | None] = mapped_column()
    seed_rate_kg_ha: Mapped[Decimal | None] = mapped_column()
    preceding_crop: Mapped[Crop | None] = mapped_column()


def to_planting_row(planting: Planting) -> PlantingRow:
    """Build the row for ``planting``.

    Field by field, for the reason ``to_field_row`` gives: the two shapes
    are allowed to diverge, and ``PlantingRow(**planting.model_dump())``
    holds only while they do not.
    """

    return PlantingRow(
        id=planting.id,
        field_id=planting.field_id,
        crop=planting.crop,
        status=planting.status,
        establishment_method=planting.establishment_method,
        variety=planting.variety,
        rootstock=planting.rootstock,
        area_ha=planting.area_ha,
        location_note=planting.location_note,
        protection=planting.protection,
        establishment_date=planting.establishment_date,
        termination_date=planting.termination_date,
        plant_density=planting.plant_density,
        seed_rate_kg_ha=planting.seed_rate_kg_ha,
        preceding_crop=planting.preceding_crop,
    )


def to_planting(row: PlantingRow) -> Planting:
    """Build the ``Planting`` for ``row``, back through the model's validators.

    Through ``Planting(...)`` and not ``model_construct``, for the reasons
    decisions/0013 gives for ``Field``. The lifecycle validator runs again
    on read, so a stored row it rejects -- a planned stand with an
    establishment date -- raises ``ValidationError`` here, by design.

    Field by field, for the same reason as ``to_planting_row``.

    Unlike ``to_field`` it reads columns only, which ``get`` has already
    loaded, so it still works after the session has closed -- as long as
    no ``commit`` in that session has expired them.
    """

    return Planting(
        id=row.id,
        field_id=row.field_id,
        crop=row.crop,
        status=row.status,
        establishment_method=row.establishment_method,
        variety=row.variety,
        rootstock=row.rootstock,
        area_ha=row.area_ha,
        location_note=row.location_note,
        protection=row.protection,
        establishment_date=row.establishment_date,
        termination_date=row.termination_date,
        plant_density=row.plant_density,
        seed_rate_kg_ha=row.seed_rate_kg_ha,
        preceding_crop=row.preceding_crop,
    )
