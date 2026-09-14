"""Connecting to a database, as opposed to defining one.

``base.py`` holds the registry every table attaches to: *what a database
is*. This file answers *which database it is*. The two have different
lifetimes -- a test builds a throwaway one per run, a deployment has
exactly one for years -- so nothing here knows an address. It is handed in.
"""

from sqlalchemy import Engine, create_engine


def build_engine(url: str) -> Engine:
    """Return a new engine for ``url``.

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

    return create_engine(url, hide_parameters=True)
