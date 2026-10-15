"""Column types of this project's own, layered over SQLAlchemy's.

Kept apart from ``base.py``, which is the registry of tables, and from the
table modules, since a type is shared by any table that stores its kind of
value.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator


class UTCDateTime(TypeDecorator[datetime]):
    """A moment in time, stored as UTC and always read back as UTC.

    SQLite has no type for a timestamp with a zone: it stores the digits and
    drops the ``tzinfo``, so an aware ``datetime`` comes back naive.
    ``DateTime(timezone=True)`` does not help, since SQLite ignores it. This
    type stands at the column and does the conversion itself, the same way on
    every backend. decisions/0018.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        """Refuse a naive datetime; store an aware one as naive UTC.

        Naive is refused rather than assumed to be UTC: it has no zone, and
        guessing one is how a stored moment ends up two hours off with no
        error anywhere. An aware value of any zone is converted, so the
        stored digits always mean UTC. The zone is then dropped, since the
        column holds digits only, on SQLite because it cannot hold more, and
        on PostgreSQL so that the two backends store the same thing.
        """

        if value is None:
            return None

        if value.tzinfo is None:
            raise ValueError(
                "A naive datetime cannot be stored: "
                "without a zone there is no way to know which UTC moment it is."
            )

        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        """Read the stored digits back as the UTC moment they were written as.

        ``replace``, not ``astimezone``: the digits are already UTC, because
        ``process_bind_param`` converted them on the way in, so this attaches
        the zone without moving the time. ``astimezone`` on a naive value would
        read it as the machine's local time and shift it by that offset.
        """

        if value is None:
            return None

        return value.replace(tzinfo=UTC)
