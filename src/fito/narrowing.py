"""The narrowing loop: which causes still stand after the answers so far.

The loop is handed the knowledge pack and the moves of one conversation,
and works out from them alone the causes still standing, what each answer
eliminated, and what happens next (decisions/0019). It keeps nothing
between calls, so the same pack and the same moves always give the same
report.

No database, no network and no model. In the skeleton an answer is one of
the words the pack offers. Reading a farmer's own words arrives with the
model, and it changes what a move records, not what this module computes
from it.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict

from fito.knowledge import KnowledgePack


class Move(BaseModel):
    """One answered question: the question's id and the answer it got.

    A move records what happened, so it is kept in the conversation's
    state and never recomputed (decisions/0019). The answer is one of the
    keys of the question's ``eliminates`` table, written as the farmer
    would type it.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        validate_assignment=True,
    )

    question_id: str
    answer: str


class TrailEntry(BaseModel):
    """One line of the trail: a move, and the causes its answer knocked down.

    ``eliminated`` lists only causes that were still standing when the
    answer came. A cause the answer names, but an earlier answer had
    already eliminated, is left out, so every eliminated cause appears in
    the trail exactly once, beside the answer that eliminated it. The trail
    therefore depends on the order of the moves, as the story of one
    conversation should. Everything an answer rules out, whatever came
    before it, is read from the pack.

    The entry carries its move instead of relying on the trail and the
    moves lining up by position: two lists matched by index go wrong
    silently.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        validate_assignment=True,
    )

    move: Move
    eliminated: list[str]


class StopReason(str, Enum):
    """Why the loop stops asking.

    ``NONE_LEFT`` is the system saying it does not recognise the problem:
    the answers ruled out every cause it knows, so the reply refers the
    farmer to an agronomist. ``QUESTIONS_EXHAUSTED`` means every question
    has been asked and several causes still stand; the reply says so and
    names them.
    """

    ONE_LEFT = "one_left"
    NONE_LEFT = "none_left"
    QUESTIONS_EXHAUSTED = "questions_exhausted"


class Ask(BaseModel):
    """The next step when the loop goes on: ask this question.

    A model around one id, rather than the bare id, so that ``next_step``
    can be told apart by type. A ``StopReason`` is a ``str`` as well
    (decisions/0001), so a bare id beside it could not be.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        validate_assignment=True,
    )

    question_id: str


class Stop(BaseModel):
    """The next step when the loop ends, and why.

    Only the reason. The cause left standing, or the several that are, are
    already in the report's ``standing``, and a second copy here could
    disagree with it.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        validate_assignment=True,
    )

    reason: StopReason


class NarrowingReport(BaseModel):
    """What the loop worked out from a pack and one conversation's moves.

    Computed again on every message and never stored (decisions/0019).
    ``standing`` follows the order of the pack, ``trail`` the order of the
    moves.

    It speaks in ids, not names. A name is what a farmer reads, and
    whoever replies to the farmer looks it up in the pack; the loop only
    reasons, as a move names its question by id.

    ``next_step`` is one field holding either an ``Ask`` or a ``Stop``. Two
    fields, a next question and a stop reason, could hold both at once or
    neither, and nothing would say that either is nonsense.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        validate_assignment=True,
    )

    standing: list[str]
    trail: list[TrailEntry]
    next_step: Ask | Stop


def narrow(pack: KnowledgePack, moves: list[Move]) -> NarrowingReport:
    """Walk a conversation's moves over the pack and report where it stands.

    The moves are walked in order. Each answer knocks down the causes it
    eliminates that are still standing, and the trail records which; a
    cause knocked down is never raised again.

    A move naming a question the pack does not have, or an answer the
    question does not accept, raises ``KeyError``. A move is made only
    after an answer has been read against the words its question offers,
    so an unknown one is a bug in whatever made it, not a farmer's typo,
    and it is not caught.
    """

    standing = [cause.id for cause in pack.causes]
    questions = {question.id: question for question in pack.questions}
    trail: list[TrailEntry] = []
    for move in moves:
        listed = questions[move.question_id].eliminates[move.answer]

        eliminated = [cause_id for cause_id in listed if cause_id in standing]
        standing = [cause_id for cause_id in standing if cause_id not in eliminated]

        trail.append(TrailEntry(move=move, eliminated=eliminated))

    return NarrowingReport(
        standing=standing, trail=trail, next_step=_next_step(pack, moves, standing)
    )


def _next_step(pack: KnowledgePack, moves: list[Move], standing: list[str]) -> Ask | Stop:
    """Whether the loop stops, and if it does not, which question comes next.

    The rules are checked in order, and the first that holds decides. One
    cause standing, or none, ends the loop even with questions left: a
    question exists to tell standing causes apart, and an eliminated cause
    never comes back. With several standing and nothing left to ask, the
    loop stops and says so.

    The next question is the first unanswered one in the pack's order. It
    is a placeholder, and it can pick a question none of whose answers
    would eliminate anything still standing; information gain replaces it
    at checkpoint 2.
    """

    asked = {move.question_id for move in moves}
    unanswered = [question.id for question in pack.questions if question.id not in asked]

    if len(standing) == 1:
        return Stop(reason=StopReason.ONE_LEFT)

    if not standing:
        return Stop(reason=StopReason.NONE_LEFT)

    if not unanswered:
        return Stop(reason=StopReason.QUESTIONS_EXHAUSTED)

    return Ask(question_id=unanswered[0])
