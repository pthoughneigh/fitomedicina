"""Tests for reading a farmer's answer.

The reader is tested on a question built here, without a pack: reading
depends only on the words a question offers. One test for each thing
it promises: an offered word is read; case does not count, and neither
do the spaces around the message; anything else is not read; and the
word comes back as the pack writes it.

The last test needs a word the pack spells differently from the farmer,
"Da" against "da". With the lowercase words a pack usually has, the
pack's word and the farmer's word cleaned up are the same string, and a
reader returning the wrong one of the two would pass every other test.
"""

from fito.knowledge import Question
from fito.reading import read_answer

QUESTION = Question(
    id="leaf_age",
    text="Žute li prvo stariji (donji) listovi ili mlađi (gornji)?",
    eliminates={"donji": [], "gornji": []},
)


def test_offered_word_is_read() -> None:
    assert read_answer(QUESTION, "donji") == "donji"


def test_case_does_not_count() -> None:
    assert read_answer(QUESTION, "Donji") == "donji"


def test_surrounding_spaces_do_not_count() -> None:
    assert read_answer(QUESTION, "  donji  ") == "donji"


def test_anything_else_is_not_read() -> None:
    assert read_answer(QUESTION, "donji listovi") is None


def test_word_comes_back_as_the_pack_writes_it() -> None:
    question = Question(
        id="powdery_stripes",
        text="Ima li na listu žutih pruga koje ostavljaju prah na prstu?",
        eliminates={"Da": [], "Ne": []},
    )

    answer = read_answer(question, "da")
    assert answer == "Da"
