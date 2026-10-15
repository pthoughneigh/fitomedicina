"""Tests that a ``Case`` comes back from the database as it went in.

The shape of ``test_planting_round_trip.py``, one floor down. Each test
writes a field, flushes, writes a planting, flushes, then writes the case,
for the reason that file gives: without a ``relationship`` the ORM orders
its INSERTs by class name, and ``CaseRow`` sorts first.

``test_case_survives_a_round_trip_through_the_database_unchanged`` is the
test that found the zone being dropped. Before ``UTCDateTime``, every
column read back equal except ``opened_at``, which came back as the same
microsecond with no ``tzinfo``: the two compared unequal, and nothing
raised. decisions/0018.

``test_naive_opened_at_is_refused`` holds the other half of that type. It
builds a ``CaseRow`` directly rather than through ``Case``, because the
model always stamps an aware value and so cannot produce the case this
guards against: code that writes rows by hand. The error surfaces as
``StatementError``, since SQLAlchemy wraps what the type raises while it
is preparing the statement.

``test_case_read_back_through_to_case_equals_the_original`` takes the
route back through ``to_case`` and compares with one ``==``, for the
reason ``test_planting_round_trip.py`` gives: a mistake made the same way
in both translations passes the comparison by column name.

``test_cases_get_deleted_when_field_is_deleted`` holds the erasure chain
two floors down: a bulk ``delete`` of the field, which the ORM never sees,
removes the planting through ``plantings``' cascade and the case through
``cases``' own. The farmer's words go with the field, inside the database,
on every path. The check reads in a third session, so that the answer
comes from the database.
"""

import uuid
from datetime import date, datetime

import pytest
from sqlalchemy import Engine, delete
from sqlalchemy.exc import StatementError
from sqlalchemy.orm import Session

from fito.db.case import CaseRow, to_case, to_case_row
from fito.db.field import FieldRow, to_field_row
from fito.db.planting import to_planting_row
from fito.schema.case import Case
from fito.schema.field import Country, Field
from fito.schema.planting import Crop, Planting


def test_case_survives_a_round_trip_through_the_database_unchanged(engine: Engine) -> None:
    field = Field(country=Country.RS)
    planting = Planting(field_id=field.id, crop=Crop.PEPPER)
    case = Case(
        planting_id=planting.id,
        initial_message="Žute mi listovi na paprici.",
        observed_on=date(2026, 10, 1),
    )

    with Session(engine) as session:
        session.add(to_field_row(field))
        session.flush()
        session.add(to_planting_row(planting))
        session.flush()
        session.add(to_case_row(case))
        session.commit()

    with Session(engine) as session:
        row = session.get(CaseRow, case.id)

        assert row is not None

        expected = case.model_dump()
        stored = {name: getattr(row, name) for name in expected}

        assert stored == expected


def test_naive_opened_at_is_refused(engine: Engine) -> None:
    field = Field(country=Country.RS)
    planting = Planting(field_id=field.id, crop=Crop.PEPPER)

    with Session(engine) as session:
        session.add(to_field_row(field))
        session.flush()
        session.add(to_planting_row(planting))
        session.commit()

    case_row = CaseRow(
        id=uuid.uuid4(),
        planting_id=planting.id,
        initial_message="Zasto mi zute listovi na paprici?",
        observed_on=None,
        opened_at=datetime(2026, 10, 14, 12, 0),
    )

    with Session(engine) as session:
        session.add(case_row)

        with pytest.raises(StatementError) as excinfo:
            session.commit()

        assert "naive" in str(excinfo.value)


def test_case_read_back_through_to_case_equals_the_original(engine: Engine) -> None:
    field = Field(country=Country.RS)
    planting = Planting(field_id=field.id, crop=Crop.PEPPER)
    case = Case(
        planting_id=planting.id,
        initial_message="Žute mi listovi na paprici.",
        observed_on=date(2026, 10, 1),
    )

    with Session(engine) as session:
        session.add(to_field_row(field))
        session.flush()
        session.add(to_planting_row(planting))
        session.flush()
        session.add(to_case_row(case))
        session.commit()

    with Session(engine) as session:
        row = session.get(CaseRow, case.id)
        assert row is not None

        assert to_case(row) == case


def test_cases_get_deleted_when_field_is_deleted(engine: Engine) -> None:
    field = Field(country=Country.RS)
    planting = Planting(field_id=field.id, crop=Crop.PEPPER)
    case = Case(
        planting_id=planting.id,
        initial_message="Žute mi listovi na paprici.",
        observed_on=date(2026, 10, 1),
    )
    with Session(engine) as session:
        session.add(to_field_row(field))
        session.flush()
        session.add(to_planting_row(planting))
        session.flush()
        session.add(to_case_row(case))
        session.commit()

    with Session(engine) as session:
        session.execute(delete(FieldRow).where(FieldRow.id == field.id))
        session.commit()

    with Session(engine) as session:
        assert session.get(CaseRow, case.id) is None
