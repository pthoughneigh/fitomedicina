"""Tests that a ``Field`` comes back from the database as it went in.

This is the only place ``FieldRow`` is checked against ``Field``.
``to_field_row`` names every column by hand, and its docstring says why, so
the comparison here takes its names from ``model_dump`` rather than keeping
a list of its own. A second hand-written list would share the first one's
blind spot: a column forgotten in one is forgotten in both, and the test
passes. Only ``cadastral_parcels`` is named, because it is a list of strings
on the model and a list of rows on the other side.

The database notices a forgotten column by itself only when it is
``NOT NULL``, and then the insert fails at commit. A nullable column fails
silently -- ``None`` written, ``None`` read -- and most of them are nullable.
That is why every attribute is set, each to a value that differs from its
default and from every other value of its type: a dropped value reads back
empty, which is what an optional attribute is by default, and a swapped pair
reads back as each other.

The read happens in a second session. In the session that added it, ``get``
hands back the very object it was given, committed or not, so a test reading
there passes whether or not anything was committed. Assertions stay inside
the second session because ``cadastral_parcels`` loads on first access, which
a closed session cannot do. Parcels are compared sorted: the child table has
no column for order, so the database promises none, and the model needs none.
"""

import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from fito.db.base import Base
from fito.db.engine import build_engine
from fito.db.field import FieldRow, to_field_row
from fito.schema.field import Country, Drainage, Field, Irrigation, Slope, SoilTexture, SoilType


def test_field_survives_a_round_trip_through_the_database_unchanged() -> None:
    engine = build_engine("sqlite://")
    Base.metadata.create_all(engine)

    field = Field(
        country=Country.RS,
        holding_id=uuid.uuid4(),
        name="Kod bare",
        latitude=Decimal("45.771234"),
        longitude=Decimal("19.351234"),
        municipality="Sombor",
        cadastral_parcels=["1234/5", "1234/6"],
        cadastral_municipality="Stanisic",
        area_ha=Decimal("4.1234"),
        soil_type=SoilType.CHERNOZEM,
        soil_texture=SoilTexture.SILT_LOAM,
        slope=Slope.GENTLE,
        irrigation=Irrigation.DRIP,
        drainage=Drainage.TILE,
    )

    with Session(engine) as session:
        session.add(to_field_row(field))
        session.commit()

    with Session(engine) as session:
        row = session.get(FieldRow, field.id)

        assert row is not None

        expected = field.model_dump(exclude={"cadastral_parcels"})
        stored = {name: getattr(row, name) for name in expected}
        assert stored == expected

        stored_parcels = sorted(parcel.parcel_number for parcel in row.cadastral_parcels)
        assert stored_parcels == sorted(field.cadastral_parcels)
