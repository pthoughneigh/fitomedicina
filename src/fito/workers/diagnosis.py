"""The diagnosis worker: where the conversation stands, from its moves.

It runs the narrowing loop over the pack and the moves the supervisor
keeps in the conversation's state, and hands the loop's report back in
a ``WorkerResult``. No database, no network and no model.
"""

from fito.knowledge import KnowledgePack
from fito.narrowing import Move, NarrowingReport, narrow
from fito.workers.result import WorkerResult


def diagnose(pack: KnowledgePack, moves: list[Move]) -> WorkerResult[NarrowingReport]:
    """Hand back the loop's report on the pack and the moves so far.

    The worker adds nothing to the report yet. It exists so that the
    supervisor calls a worker, not the loop: at checkpoint 2 the worker
    grows, as probabilities replace elimination, and the call stays the
    same.

    It is not given the prior, though the risk worker computes one when
    a conversation starts and the supervisor records it in the state.
    Elimination needs no head start: an answer knocks a cause down
    whatever its share. The prior waits in the state until checkpoint 2,
    when it becomes the starting probabilities and a parameter here.

    The moves arrive already read: each answer is one of the words its
    question offers, and reading what the farmer typed is not this
    worker's job. A move the pack does not know raises the loop's
    ``KeyError``, uncaught, since it is a bug in whatever made the move.
    """
    return WorkerResult(data=narrow(pack, moves))
