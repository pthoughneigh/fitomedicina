"""Tests for the diagnosis worker.

The worker hands back the loop's report and adds nothing, so its one
test compares the two: the worker's data against ``narrow`` called on the
same pack and moves. The loop's own rules are tested in
``test_narrowing.py``. Repeating them here would test the loop twice, and
both copies would have to change when the loop does at checkpoint 2.

The move knocks a cause down, so the report after it differs from the
report before any answer, and a worker that dropped the moves would fail.
"""

import tomllib

from fito.knowledge import KnowledgePack
from fito.narrowing import Move, narrow
from fito.workers.diagnosis import diagnose

PACK = KnowledgePack.model_validate(
    tomllib.loads("""
    illustrative = true

    [[causes]]
    id = "a"
    name = "a"

    [[causes]]
    id = "b"
    name = "b"

    [[questions]]
    id = "first"
    text = "Prvo pitanje?"
    eliminates = { da = ["a"], ne = ["b"] }
    """)
)


def test_worker_hands_back_the_loops_report() -> None:
    moves = [Move(question_id="first", answer="da")]
    result = diagnose(PACK, moves)

    assert result.data == narrow(PACK, moves)
