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
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from fito.knowledge import KnowledgePack, load_pack

WHEAT_PACK = Path(__file__).resolve().parents[1] / "knowledge" / "wheat.toml"


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
