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

    with Path(path).open("rb") as file:
        return KnowledgePack.model_validate(tomllib.load(file))
