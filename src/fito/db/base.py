"""The declarative registry every ORM model is attached to.

Table definitions live beside it, one module per entity, and the engine
in ``engine.py``. Defining a table and connecting to a database are
separate concerns with different lifetimes in a test suite, so they are
kept apart by module rather than by package.
"""

import enum
from collections.abc import Sequence
from typing import Any, ClassVar

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Templates are the canonical set from the SQLAlchemy and Alembic docs.
SQL_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def enum_values(enum_class: type[enum.Enum]) -> Sequence[str]:
    """Return the strings an enum's members are stored as.

    SQLAlchemy stores a member's *name* by default. This project stores its
    *value*, because the values are the external code lists -- ISO country
    codes, WRB soil groups -- while the names are only Python identifiers.
    """
    return [member.value for member in enum_class]


class Base(DeclarativeBase):
    """The single declarative registry for the whole project.

    Subclassing this is not inheritance in the usual sense -- no behaviour
    is handed down. It is registration: a subclass adds itself to
    ``Base.metadata``, the catalogue that ``create_all`` reads to emit
    ``CREATE TABLE`` and that a migration tool later diffs against the
    real database.

    One registry, project-wide. Foreign keys resolve by table name within
    a single ``MetaData``, so two registries cannot see each other and a
    reference across them fails to resolve.

    That includes the regulatory reference tables, which arrive from
    outside, are versioned by publication date and are never subject to an
    erasure request. A different lifetime is a reason for different
    cascades and different naming, not for a second registry.

    Constraint names are chosen here rather than by the database, through
    ``naming_convention`` on the metadata below. Left to itself, each
    backend invents its own: PostgreSQL produces
    ``fields_holding_id_fkey``, SQLite frequently produces nothing at all.
    That is invisible while tables are only ever created, and becomes a
    problem the first time a migration has to drop a constraint, which it
    can only do by name. Development runs on SQLite and deployment on
    PostgreSQL, so a migration written against one would carry a name the
    other has never heard of.
    """

    metadata = MetaData(naming_convention=SQL_NAMING_CONVENTION)

    type_annotation_map: ClassVar[dict[Any, Any]] = {
        enum.Enum: SQLEnum(enum.Enum, native_enum=False, values_callable=enum_values),
    }
