"""The knowledge pack: what the narrowing loop knows about one crop.

A pack is read from a TOML file in ``knowledge/``, one file per crop, and
checked here before anything uses it (decisions/0020). It is content this
project writes, not data a farmer enters, which is why it sits beside
``schema/`` rather than in it: nothing here is personal data, and nothing
here goes into the database.
"""

import tomllib
from pathlib import Path
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator


class Cause(BaseModel):
    """One possible cause of a symptom.

    ``id`` is how the rest of the pack refers to it; ``name`` is what a
    farmer reads.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        validate_assignment=True,
    )

    # A plain string, not an enum. A cause is content, and adding one must
    # not need a code change (decisions/0020).
    id: str
    name: str


class Question(BaseModel):
    """A question that tells causes apart, and what each answer rules out."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        validate_assignment=True,
    )
    id: str
    text: str
    # Each key is an answer the question accepts, written as the farmer
    # types it; its value lists the causes that answer eliminates. A cause
    # an answer does not list is one the answer says nothing about, and an
    # answer that rules nothing out is still listed, with an empty list
    # (decisions/0020).
    eliminates: dict[str, list[str]]


class KnowledgePack(BaseModel):
    """Everything the narrowing loop knows about one crop and one symptom.

    Only ever read. The causes still standing in a conversation are
    computed from the pack and the moves on every message, never written
    back into the pack (decisions/0019).
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        validate_assignment=True,
    )
    # Required, with no default: a pack that forgets to say it is an
    # illustration must fail to load rather than pass as knowledge. TOML
    # gives a key placed below the first ``[[causes]]`` to that cause, so a
    # misplaced flag fails twice: as missing here and as unknown there.
    illustrative: bool
    causes: list[Cause]
    questions: list[Question]

    @model_validator(mode="after")
    def _check_eliminated_causes_exist(self) -> Self:
        """Reject an answer that eliminates a cause the pack does not define.

        Without this, a typo in a cause id is not an error: the answer names
        a cause that does not exist, the cause that was meant is never
        eliminated, and the loop narrows less than the pack says it should,
        with nothing to tell why. The check spans the causes and the
        questions, so it runs on the whole pack, after each part has passed
        its own field checks.

        It stops at the first unknown id rather than collecting them all. A
        pack is written by hand and fixed one line at a time, and the other
        validators in this project stop at the first problem too.

        The reverse is allowed. A cause that no answer eliminates is legal:
        silence means an answer says nothing about a cause (decisions/0020),
        and such a cause can still be the one left standing once the others
        fall.
        """

        cause_ids = {cause.id for cause in self.causes}
        for question in self.questions:
            for answer, eliminated in question.eliminates.items():
                for cause_id in eliminated:
                    if cause_id not in cause_ids:
                        raise ValueError(
                            f"Answer {answer!r} to question {question.id!r} eliminates "
                            f"{cause_id!r}, which is not a cause in this pack."
                        )
        return self

    @model_validator(mode="after")
    def _check_ids_are_unique(self) -> Self:
        """Reject a cause id or a question id that appears more than once.

        Copying a block to start the next one is how a pack grows, and an id
        left unchanged is the likeliest slip. Both kinds of id are keys the
        rest of the system looks things up by. Two causes under one id
        collapse into one candidate, and one of them can never be named.
        Two questions under one id make a recorded move ambiguous, since a
        move names its question by id (decisions/0019).

        The first rule cannot see this: a duplicated cause still exists.

        Answers need no such check. They are the keys of a table, so they
        cannot repeat: TOML refuses a key written twice, with ``Cannot
        overwrite a value`` (measured), and a Python dict cannot hold one
        twice either.
        """
        seen_causes = set()
        for cause in self.causes:
            if cause.id in seen_causes:
                raise ValueError(f"Cause id {cause.id!r} appears more than once.")
            seen_causes.add(cause.id)

        seen_questions = set()
        for question in self.questions:
            if question.id in seen_questions:
                raise ValueError(f"Question id {question.id!r} appears more than once.")
            seen_questions.add(question.id)

        return self


def load_pack(path: Path) -> KnowledgePack:
    """Read the knowledge pack at ``path`` and check it.

    The path is handed in, as ``build_engine`` is handed a URL: this module
    says what a pack is, and which file holds one is the caller's decision.
    The CLI will name ``knowledge/wheat.toml``; a test can name its own.

    The file is opened in binary mode because ``tomllib`` decodes the bytes
    itself, as UTF-8, and refuses a text-mode file. A byte-order mark at the
    start fails loudly, as ``Invalid statement (at line 1, column 1)``:
    measured, and the place to look when a pack saved by another editor
    will not load.

    Neither error is caught. Broken TOML raises ``TOMLDecodeError`` and a
    broken pack raises ``ValidationError``, and both should stop the program
    before a conversation starts: the fix belongs in the file, not here.
    """

    with path.open("rb") as file:
        return KnowledgePack.model_validate(tomllib.load(file))
