"""Tests for the checks on a knowledge pack, and for the pack itself.

The rules are tested on packs built here from dictionaries, as
``test_field.py`` builds a ``Field`` without a database: a rule of the
model is tested in the model, with input shaped to make that one rule fire.

``test_answer_eliminating_an_unknown_cause_raises`` holds the rule
decisions/0020 sets: an answer may eliminate only a cause the pack defines.
Without it, a typo in a cause id is not an error but a cause that is never
eliminated. The loop runs, the farmer answers, and the cause stays standing
for a reason nobody can see. The rule spans two parts of the pack, its
causes and its questions, so it belongs to ``KnowledgePack`` as a whole,
and its error carries an empty ``loc``. The message, which names the
unknown id, is what the test reads. The pack in it is valid in every other
respect, and ``len(errors) == 1`` is what says so: a missing key would
raise as well, and pass the test for the wrong reason.

``test_wheat_pack_is_marked_as_an_illustration`` reads the real file,
through ``load_pack``, the way the program will. It is the test
decisions/0020 promises: a broken pack fails the suite rather than the
first conversation. What it asserts is the skeleton's honesty. The pack's
content is invented, and until checkpoint 2 replaces it, the program has
to know that. The assertion is meant to change on that day, by hand,
together with the content. The path is built from this file's own
location, so the test finds the pack whichever folder pytest is started
from.

``test_two_causes_with_the_same_id_raise`` and
``test_two_questions_with_the_same_id_raise`` hold the second rule: every
id appears once. Copying a block to start the next one is how a pack
grows, and an id left unchanged is the likeliest slip in a file written by
hand. The first rule cannot see it, since a duplicated cause still exists.
Two rules on ``KnowledgePack`` now raise the same ``value_error`` with the
same empty ``loc``, so each test asserts the sentence of its own rule, not
only the id.

``test_load_pack_reads_the_path_it_is_given`` holds the promise in
``load_pack``'s signature: the file it reads is the one it is handed. The
test of the real pack cannot see this, since a function that always opens
``knowledge/wheat.toml`` passes it, and one did, until the suite was run
from inside ``tests/``. Here the pack is a different one, written for the
test into ``tmp_path``, the empty folder pytest gives each test that asks
for it, and the assertion is on its one cause. It is written as UTF-8
explicitly: on Windows Python writes text in the system's code page by
default, and ``tomllib`` reads only UTF-8.

``test_pack_without_causes_raises`` holds the third rule: a pack has at
least one cause. Without it an empty pack loads, and each reader fails
in its own way: the loop stops at once with ``NONE_LEFT``, saying every
cause was ruled out when there was none, and the risk worker divides by
zero, two steps from the file that is wrong. It is a constraint on one
field, not a model validator, so its error has an address,
``("causes",)``, and Pydantic's own type, ``too_short``, which is what
the test reads. Questions get no such rule: a pack whose one cause needs
no question is legal, and ``test_risk.py`` uses a pack with none.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from fito.knowledge import KnowledgePack, load_pack

WHEAT_PACK = Path(__file__).resolve().parents[1] / "knowledge" / "wheat.toml"
FROST_PACK = """
    illustrative = true

    [[causes]]
    id = "frost"
    name = "mraz"

    [[questions]]
    id = "cold_night"
    text = "Je li se javilo posle hladne noći?"

    [questions.eliminates]
    da = []
    ne = ["frost"]
"""


def test_answer_eliminating_an_unknown_cause_raises() -> None:
    pack = {
        "illustrative": True,
        "causes": [{"id": "nitrogen_deficiency", "name": "nedostatak azota"}],
        "questions": [
            {
                "id": "leaf_age",
                "text": "Žute li prvo stariji (donji) listovi ili mlađi (gornji)?",
                "eliminates": {"donji": ["sulfur_deficiency"]},
            }
        ],
    }

    with pytest.raises(ValidationError) as excinfo:
        KnowledgePack.model_validate(pack)

    errors = excinfo.value.errors()
    assert len(errors) == 1
    assert errors[0]["type"] == "value_error"
    assert errors[0]["loc"] == ()
    assert "sulfur_deficiency" in errors[0]["msg"]


def test_wheat_pack_is_marked_as_an_illustration() -> None:
    pack = load_pack(WHEAT_PACK)
    assert pack.illustrative


def test_two_causes_with_the_same_id_raise() -> None:
    pack = {
        "illustrative": True,
        "causes": [
            {"id": "nitrogen_deficiency", "name": "nedostatak azota"},
            {"id": "nitrogen_deficiency", "name": "nedostatak sumpora"},
        ],
        "questions": [
            {
                "id": "leaf_age",
                "text": "Žute li prvo stariji (donji) listovi ili mlađi (gornji)?",
                "eliminates": {"donji": [], "gornji": ["nitrogen_deficiency"]},
            }
        ],
    }

    with pytest.raises(ValidationError) as excinfo:
        KnowledgePack.model_validate(pack)

    errors = excinfo.value.errors()
    assert len(errors) == 1
    assert errors[0]["type"] == "value_error"
    assert errors[0]["loc"] == ()
    assert "Cause id 'nitrogen_deficiency' appears more than once" in errors[0]["msg"]


def test_two_questions_with_the_same_id_raise() -> None:
    pack = {
        "illustrative": True,
        "causes": [{"id": "nitrogen_deficiency", "name": "nedostatak azota"}],
        "questions": [
            {
                "id": "leaf_age",
                "text": "Žute li prvo stariji (donji) listovi ili mlađi (gornji)?",
                "eliminates": {"da": ["nitrogen_deficiency"]},
            },
            {
                "id": "leaf_age",
                "text": "Ima li na listu žutih pruga koje ostavljaju prah na prstu?",
                "eliminates": {"ne": ["nitrogen_deficiency"]},
            },
        ],
    }

    with pytest.raises(ValidationError) as excinfo:
        KnowledgePack.model_validate(pack)

    errors = excinfo.value.errors()
    assert len(errors) == 1
    assert errors[0]["type"] == "value_error"
    assert errors[0]["loc"] == ()
    assert "Question id 'leaf_age' appears more than once" in errors[0]["msg"]


def test_load_pack_reads_the_path_it_is_given(tmp_path: Path) -> None:
    pack_file = tmp_path / "frost.toml"
    pack_file.write_text(FROST_PACK, encoding="utf-8")
    pack = load_pack(pack_file)

    assert [cause.id for cause in pack.causes] == ["frost"]


def test_pack_without_causes_raises() -> None:
    with pytest.raises(ValidationError) as excinfo:
        KnowledgePack.model_validate({"illustrative": True, "causes": [], "questions": []})

    errors = excinfo.value.errors()
    assert len(errors) == 1
    assert errors[0]["type"] == "too_short"
    assert errors[0]["loc"] == ("causes",)
