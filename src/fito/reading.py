"""Reading a farmer's answer against the words its question offers.

The one place where what the farmer typed becomes the answer of a move.
In the skeleton it compares the message with the offered words and
reads nothing else. The model replaces it here, the first fake to go,
and brings the pseudonymization boundary and a repeated-run eval with
it. No database, no network and no model yet.
"""

from fito.knowledge import Question


def read_answer(question: Question, message: str) -> str | None:
    """Return the offered word the message is, or ``None`` if it is none.

    Case and the spaces around the message do not count; anything else
    does, so "donji listovi" or "Da." is not read. That is deliberate:
    this reader never reads an answer wrongly, it only sometimes asks
    again. A wrong reading would knock down a cause the farmer never
    ruled out, perhaps the true one, where asking again costs one more
    message. ``None`` means only "not read", and the supervisor answers
    it by asking again.

    The word comes back as the pack writes it, not as the farmer did,
    because the loop looks the answer up in ``eliminates`` by that key.
    """
    cleaned = message.strip().lower()
    for word in question.eliminates:
        if word.lower() == cleaned:
            return word
    return None
