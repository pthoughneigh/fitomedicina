"""Logging configuration for the whole project.

Called by the application entry point and by ``conftest.py``, and by nothing
else. A library module asks for a logger and writes to it; deciding the format,
the level and the destination belongs to whatever starts the process.

``force=True`` below reflects that: the caller is an owner, not a guest, so it
replaces whatever handlers are already on the root. Pytest installs its own
before ``conftest.py`` runs, and without ``force`` this function would silently
do nothing there.
"""

import logging


def configure_logging(*, level: int = logging.INFO, show_sql: bool = False) -> None:
    """Send logs to the console and set how loud SQLAlchemy is.

    ``show_sql`` turns on statement logging from the engine. Off by default:
    the quieter setting is the one you get when nobody has thought about it.
    ``DEBUG`` on that logger is deliberately not offered -- it prints result
    rows, which is the data itself.

    Statements are logged without their bound parameters unless the engine
    was built to include them. That decision lives at ``create_engine``, with
    ``hide_parameters``, because parameters are field coordinates and farmer
    text -- a second copy of personal data, on disk, outside any erasure
    cascade. Local only.
    """
    logging.basicConfig(
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", level=level, force=True
    )
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO if show_sql else logging.WARNING)
