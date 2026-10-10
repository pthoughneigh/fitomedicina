"""Tests that a ``Planting`` comes back from the database as it went in.

The same shape as ``test_field_round_trip.py`` for ``Field``, and for the
same reasons: names are taken from ``model_dump`` rather than listed by
hand, and every attribute is set, each to a value that differs from its
default and from every other value of its type, so that a dropped value
reads back empty and a swapped pair reads back as each other. The values
are chosen to be distinct, not agronomically consistent: a transplanted
pepper has no seed rate.

Each test writes a ``Field`` before its planting, in that order and in
one session: the foreign key refuses a planting that points at nothing,
and without a ``relationship`` the ORM writes rows in the order they
were added.

``test_planting_read_back_through_to_planting_equals_the_original`` takes
the route back through ``to_planting`` and compares with one ``==``. It
sits beside the first test for the reason ``test_field_round_trip.py``
gives: a mistake made the same way in both translations passes any round
trip, and only the comparison by column name sees it. With the two dates
swapped in both ``to_planting_row`` and ``to_planting``, only the first
test goes red; with ``variety`` dropped from ``to_planting`` alone, only
this one does.

``test_planting_pointing_at_a_nonexistent_field_is_refused`` holds the
foreign key on ``plantings``. The planting is built through the model and
``to_planting_row``, the route the application will take: ``Planting``
checks that ``field_id`` is a UUID, not that such a field exists, so only
the database can refuse it. The assertion reads SQLite's message, for the
reason ``test_field_round_trip.py`` gives.

``test_plantings_get_deleted_when_field_is_deleted`` holds the erasure
rule from decisions/0016. The field is deleted with a bulk ``delete``,
which the ORM never sees, because that is the one path only the database
can cover: if the planting is gone afterwards, the rule lives in the
database. ``session.delete`` reaches the same rule, since ``FieldRow``
knows nothing of plantings. The field has no parcels, which only the ORM
deletes; with parcels the bulk delete would be refused. The check reads
in a third session, so that the answer comes from the database.

Broken both ways, the test goes red in two different places. Without
``ondelete="CASCADE"`` the bulk delete itself is refused, with
``IntegrityError``. Without the foreign-key pragma the delete goes
through, the planting stays behind and nothing raises: only the check
at the end fails, and without it the test passed.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import Engine, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fito.db.field import FieldRow, to_field_row
from fito.db.planting import PlantingRow, to_planting, to_planting_row
from fito.schema.field import Country, Field
from fito.schema.planting import Crop, EstablishmentMethod, Planting, PlantingStatus, Protection


def test_planting_survives_a_round_trip_through_the_database_unchanged(engine: Engine) -> None:
    field = Field(country=Country.RS)

    planting = Planting(
        field_id=field.id,
        crop=Crop.PEPPER,
        preceding_crop=Crop.WHEAT,
        status=PlantingStatus.TERMINATED,
        establishment_method=EstablishmentMethod.TRANSPLANTED,
        protection=Protection.TUNNEL,
        variety="Kurtovska kapija",
        rootstock="vigorous hybrid",
        location_note="the two tunnels",
        area_ha=Decimal("0.2345"),
        seed_rate_kg_ha=Decimal("1.25"),
        establishment_date=date(2026, 4, 20),
        termination_date=date(2026, 10, 5),
        plant_density=35000,
    )

    with Session(engine) as session:
        session.add(to_field_row(field))
        session.add(to_planting_row(planting))
        session.commit()

    with Session(engine) as session:
        row = session.get(PlantingRow, planting.id)
        assert row is not None

        expected = planting.model_dump()
        stored = {name: getattr(row, name) for name in expected}
        assert stored == expected


def test_planting_read_back_through_to_planting_equals_the_original(engine: Engine) -> None:
    field = Field(country=Country.RS)

    planting = Planting(
        field_id=field.id,
        crop=Crop.PEPPER,
        preceding_crop=Crop.WHEAT,
        status=PlantingStatus.TERMINATED,
        establishment_method=EstablishmentMethod.TRANSPLANTED,
        protection=Protection.TUNNEL,
        variety="Kurtovska kapija",
        rootstock="vigorous hybrid",
        location_note="the two tunnels",
        area_ha=Decimal("0.2345"),
        seed_rate_kg_ha=Decimal("1.25"),
        establishment_date=date(2026, 4, 20),
        termination_date=date(2026, 10, 5),
        plant_density=35000,
    )

    with Session(engine) as session:
        session.add(to_field_row(field))
        session.add(to_planting_row(planting))
        session.commit()

    with Session(engine) as session:
        row = session.get(PlantingRow, planting.id)
        assert row is not None
        assert to_planting(row) == planting


def test_planting_pointing_at_a_nonexistent_field_is_refused(engine: Engine) -> None:
    planting = Planting(
        field_id=uuid.uuid4(),
        crop=Crop.WHEAT,
        status=PlantingStatus.ESTABLISHED,
        establishment_method=EstablishmentMethod.DIRECT_SOWN,
    )

    with Session(engine) as session:
        session.add(to_planting_row(planting))

        with pytest.raises(IntegrityError) as excinfo:
            session.commit()

        assert "FOREIGN KEY constraint failed" in str(excinfo.value)


def test_plantings_get_deleted_when_field_is_deleted(engine: Engine) -> None:
    field = Field(country=Country.RS)

    planting = Planting(
        field_id=field.id,
        crop=Crop.WHEAT,
        status=PlantingStatus.ESTABLISHED,
        establishment_method=EstablishmentMethod.DIRECT_SOWN,
    )

    with Session(engine) as session:
        session.add(to_field_row(field))
        session.add(to_planting_row(planting))
        session.commit()

    with Session(engine) as session:
        session.execute(delete(FieldRow).where(FieldRow.id == field.id))
        session.commit()

    with Session(engine) as session:
        assert session.get(PlantingRow, planting.id) is None
