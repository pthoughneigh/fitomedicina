"""The ``fields`` table: the stored shape of a field.

Deliberately a separate class from ``fito.schema.field.Field``. The validated
model and the stored row are allowed to diverge -- the pseudonymised payload
that leaves the country is not the row that stays behind -- and one file per
layer keeps that divergence visible instead of looking like duplication.
"""

import uuid

from sqlalchemy.orm import Mapped, mapped_column

from fito.db.base import Base


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
