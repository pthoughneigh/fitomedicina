"""The risk worker: how likely each cause is before the first question.

From checkpoint 3 this worker reads weather and soil, and some causes
start ahead: a long spell of wet leaves makes a fungal cause likelier
before anything has been asked. The supervisor will call it once, when a
conversation starts, and record what it returned in the conversation's
state (decisions/0019), so that every later message reasons from the
same start, even if the weather has changed since.

In the skeleton it knows no weather, so every cause starts level. No
database, no network and no model.
"""

from fito.knowledge import KnowledgePack


def assess_risk(pack: KnowledgePack) -> dict[str, float]:
    """Return the prior: the probability of each cause before any answer.

    Its shape is the contract the real worker will keep: one probability
    for every cause in the pack and for nothing else, each above zero,
    summing to one, keyed by cause id. Keyed rather than listed in the
    pack's order, for the reason ``TrailEntry`` carries its move: two
    lists matched by position go wrong silently.

    Each share is above zero however unlikely the weather makes its
    cause: an unlikely cause gets a small share, never none. Only an
    answer knocks a cause down, and the trail records it beside that
    answer. A zero here would remove a cause before the first question,
    with no line in the trail to say why. It would also be final: from
    checkpoint 2 every answer multiplies the probabilities, and zero
    times anything is zero.

    The pack is the only parameter because it is all the skeleton reads.
    What the real worker will need besides it (a grid cell, a planting,
    the day the symptom was seen) is not known yet, and is added when it
    is.

    Every cause gets the same share. Any other split would be a head
    start with no reason behind it: information the system does not
    have. Nothing reads these numbers yet, since elimination needs no
    head start and an eliminated cause is out whatever its share. They
    exist from the start so that the state keeps its shape at checkpoint
    2, when probabilities replace elimination.

    ``float``, not the ``Decimal`` that areas use. An area is a recorded
    measure, summed and compared exactly. These are computed shares,
    which checkpoint 2 will multiply and take logarithms of with NumPy
    and SciPy (decisions/0022), and 1/3 has no exact form in either type.
    """
    # Never a division by zero: a pack with no causes does not load.
    share = 1 / len(pack.causes)
    return {cause.id: share for cause in pack.causes}
