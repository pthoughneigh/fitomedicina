"""Tests for the narrowing loop.

The loop is tested on a pack written here, not on ``knowledge/wheat.toml``,
for the reason ``test_knowledge.py`` gives for its rules: a rule is tested
with input shaped to make it fire. The wheat pack is content, invented for
the skeleton and replaced with real agronomy at checkpoint 2, and a loop
test tied to it would fail that day with nothing wrong in the loop. It
cannot reach ``NONE_LEFT`` either: no combination of its answers, with
each question answered at most once, rules out all four causes.

The pack's ids are abstract on purpose, so that nothing here is read as
agronomy. Every outcome comes from a conversation the loop would actually
hold: the first question is answered first, and the second only while
more than one cause stands. ``"ne znam"`` is the answer that rules
nothing out, which is why its list is empty.

``test_conversation_played_one_move_at_a_time`` calls ``narrow`` after
every move, with the list of moves one longer each time, as the supervisor
will on every message (decisions/0019). It holds three things, in the
order a conversation meets them: the next question is the first
unanswered one, the trail leaves out a cause an earlier answer already
eliminated (``second=da`` names ``a`` again, and only ``b`` is recorded),
and one cause standing ends the loop.
"""

import tomllib

from fito.knowledge import KnowledgePack
from fito.narrowing import Ask, Move, Stop, StopReason, narrow

PACK = KnowledgePack.model_validate(
    tomllib.loads("""
    illustrative = true

    [[causes]]
    id = "a"
    name = "a"

    [[causes]]
    id = "b"
    name = "b"

    [[causes]]
    id = "c"
    name = "c"

    [[questions]]
    id = "first"
    text = "Prvo pitanje?"
    eliminates = { da = ["a"], ne = ["b", "c"] }

    [[questions]]
    id = "second"
    text = "Drugo pitanje?"
    eliminates = { da = ["a", "b"], ne = ["b", "c"], "ne znam" = [] }
    """)
)


def test_conversation_played_one_move_at_a_time() -> None:
    moves: list[Move] = []
    report = narrow(PACK, moves)

    assert report.standing == ["a", "b", "c"]
    assert report.next_step == Ask(question_id="first")

    moves.append(Move(question_id="first", answer="da"))
    report = narrow(PACK, moves)

    assert report.standing == ["b", "c"]
    assert report.next_step == Ask(question_id="second")

    moves.append(Move(question_id="second", answer="da"))
    report = narrow(PACK, moves)

    assert report.standing == ["c"]
    assert [entry.eliminated for entry in report.trail] == [["a"], ["b"]]
    assert report.next_step == Stop(reason=StopReason.ONE_LEFT)
