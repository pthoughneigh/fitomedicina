"""Fixtures shared by every test module, found by pytest without an import.

``engine`` gives each test its own database: SQLite in memory, built by
``build_engine`` so that the foreign-key pragma is on, and empty at the
start. Which tables it holds depends on which table modules have been
imported by the time the test runs -- decisions/0015.
"""

import pytest
from sqlalchemy import Engine

from fito.db.base import Base
from fito.db.engine import build_engine


@pytest.fixture
def engine() -> Engine:
    """A fresh in-memory database for one test, foreign keys on."""

    engine = build_engine("sqlite://")
    Base.metadata.create_all(engine)
    return engine
