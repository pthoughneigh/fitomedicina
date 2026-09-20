"""Connecting to a database, as opposed to defining one.

``base.py`` holds the registry every table attaches to: *what a database
is*. This file answers *which database it is*. The two have different
lifetimes -- a test builds a throwaway one per run, a deployment has
exactly one for years -- so nothing here knows an address. It is handed in.
"""

import sqlite3

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.pool import ConnectionPoolEntry


def _enable_foreign_keys(dbapi_connection: sqlite3.Connection, _: ConnectionPoolEntry) -> None:
    """Turn foreign key enforcement on for one SQLite connection.

    SQLite parses ``REFERENCES`` and then ignores it. The constraint is
    recorded in the schema and acted on only while ``foreign_keys`` is on,
    and it is off by default, so a parcel pointing at a field that does not
    exist inserts cleanly. ``fk_cadastral_parcels_field_id_fields`` is
    written into both backends; PostgreSQL enforces it and SQLite does not.

    The setting lives in the connection, not in the file. It reads ``0`` on
    every connection SQLite opens, whatever the previous one set, so there
    is no moment at startup where it could be switched on once and left.
    Hence a listener: the code that opens connections belongs to
    SQLAlchemy, and this is the only hook that reaches every one of them.

    Not ``first_connect``, which fires once. Every connection the pool
    opened after it would start at ``0`` again, and the constraint would
    hold only until the suite ran two at a time -- a failure that would
    look like flakiness rather than like this.

    The statement goes through a cursor as a plain string because this runs
    below SQLAlchemy. The ``connect`` event fires the instant the driver
    hands the connection over, before SQLAlchemy wraps it, so the argument
    is a ``sqlite3.Connection`` and ``text()`` -- which builds an object
    only SQLAlchemy reads -- has nothing here that would take it.

    The pool entry is part of the signature SQLAlchemy calls with. It is
    accepted and unused.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def build_engine(url: str) -> Engine:
    """Return a new engine for ``url``.

    The foreign key pragma is attached here, and only on SQLite. The check
    sits at attach time rather than inside the handler because the answer
    cannot change: the URL fixed the dialect when the engine was built and
    it holds for the engine's life. Asking once is enough, and it leaves
    PostgreSQL with no listener at all rather than one that runs on every
    connection to conclude it has nothing to do.

    It has to be a condition rather than a guard inside the statement.
    ``PRAGMA`` is SQLite's word; PostgreSQL would raise on it, on every
    connection. This is the first place where the split recorded in
    ``0012`` is code instead of prose.

    ``build_`` rather than ``get_``: nothing is cached and nothing is
    looked up, and a new engine comes back on every call. The URL is a
    parameter so that the same code serves ``sqlite://`` in a test and a
    real address in production.

    Nothing connects here. ``create_engine`` records the address and opens
    nothing; the first connection happens on first use. That is what makes
    this cheap to call from a fixture.

    ``hide_parameters`` is fixed on. Bound parameters are coordinates,
    field names and eventually ``Case.initial_message`` -- a second copy of
    personal data, on disk, outside every erasure cascade and harder to
    erase from a log than from a table. SQLAlchemy prints them by default,
    so this is passed rather than omitted.

    It is hardcoded rather than exposed as a flag because nothing would
    read the flag. ``configure_logging`` takes ``show_sql`` because the
    engine logger was a real consumer from day one; there is no equivalent
    here. Not ``if production: hide`` either -- a question whose wrong
    answer leaks. Revisit the first time local debugging genuinely needs
    the values, and change this line rather than the call sites.
    """

    engine = create_engine(url, hide_parameters=True)

    if engine.dialect.name == "sqlite":
        event.listen(engine, "connect", _enable_foreign_keys)

    return engine
