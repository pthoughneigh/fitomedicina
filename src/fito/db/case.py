"""The ``cases`` table: the stored shape of a case.

A separate class from ``fito.schema.case.Case``, for the reason
``fito.db.field`` gives: the validated model and the stored row are
allowed to diverge, and one file per layer keeps that visible.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from fito.db.base import Base
from fito.db.types import UTCDateTime
from fito.schema.case import Case


class CaseRow(Base):
    """One row in ``cases``.

    Validation lives in ``fito.schema.case.Case``, not here: this class
    stores what it is handed, an empty message included. No column has a
    default. The model mints ``id`` and stamps ``opened_at``, and a
    second default here would be a second clock that could disagree with
    the first.
    """

    __tablename__ = "cases"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    # Deleting a planting deletes its cases in the database itself, through
    # ``ON DELETE CASCADE``, and deleting a field reaches them through the
    # plantings' own cascade: field -> plantings -> cases, inside the
    # database, on every path. ``initial_message`` is the farmer's own words,
    # the first thing an erasure request has to reach. As with plantings,
    # SQLite honours this only on connections with foreign keys on, and
    # without them the words stay behind, silently. No ``relationship``:
    # nothing reads cases through their planting yet. decisions/0016.
    planting_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("plantings.id", ondelete="CASCADE"))
    initial_message: Mapped[str] = mapped_column()
    observed_on: Mapped[date | None] = mapped_column()
    # ``UTCDateTime``, not the ``DateTime`` that ``Mapped[datetime]`` would
    # give: SQLite drops the zone, and this column must come back aware and in
    # UTC (decisions/0006). The type refuses a naive value on the way in.
    # decisions/0018.
    opened_at: Mapped[datetime] = mapped_column(UTCDateTime())


def to_case_row(case: Case) -> CaseRow:
    """Build the row for ``case``.

    Field by field, for the reason ``to_field_row`` gives: the two shapes
    are allowed to diverge, and ``CaseRow(**case.model_dump())`` holds
    only while they do not.
    """

    return CaseRow(
        id=case.id,
        planting_id=case.planting_id,
        initial_message=case.initial_message,
        observed_on=case.observed_on,
        opened_at=case.opened_at,
    )


def to_case(row: CaseRow) -> Case:
    """Build the ``Case`` for ``row``, back through the model's validators.

    Through ``Case(...)`` and not ``model_construct``, for the reasons
    decisions/0013 gives for ``Field``. ``opened_at`` arrives aware and in
    UTC, because ``UTCDateTime`` reattaches the zone on read
    (decisions/0018); without that the model would accept the naive value
    and the case would compare unequal to the one that was written.

    Field by field, for the same reason as ``to_case_row``.
    """

    return Case(
        id=row.id,
        planting_id=row.planting_id,
        initial_message=row.initial_message,
        observed_on=row.observed_on,
        opened_at=row.opened_at,
    )
