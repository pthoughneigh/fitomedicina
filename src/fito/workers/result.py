"""What a worker hands back to the supervisor.

Every worker returns its result in the same envelope, so the supervisor
reads every worker the same way, and a fact that reaches the farmer is
always taken from the same place: the data a worker computed.
"""

from pydantic import BaseModel, ConfigDict


class WorkerResult[T](BaseModel):
    """A worker's result: the data it computed, and nothing else yet.

    The parameter names what the data is. The risk worker's prior is a
    ``WorkerResult[dict[str, float]]``, the diagnosis worker's report a
    ``WorkerResult[NarrowingReport]``, and mypy checks what goes in
    against it (``init_typed`` in pyproject.toml).

    One channel, where the earlier system had two: a summary written by a
    model, fallible and used for routing, and data captured by code, the
    only source of a fact that reaches a user. In the skeleton no worker
    has a model inside, and code decides whether to keep asking, so a
    summary would have no writer and no reader. Written by code from a
    template, it would give one field two meanings; always empty, it
    would be a field nothing reads. The rule the two channels exist for
    already holds: what reaches the farmer is read from ``data``. The
    summary arrives with the first worker whose result a model writes.

    ``data``, not ``raw_data`` as in the earlier system: what a worker
    hands back here is computed, a prior or a report, not raw.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        validate_assignment=True,
    )

    data: T
