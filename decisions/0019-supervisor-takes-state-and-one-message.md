# 0019 — The supervisor takes the state and one message

**Date:** 2026-10-21
**Status:** accepted

## Context
Checkpoint 1 needs a supervisor, and its signature is the first question
§18 sets for it. The conversation it runs is interruptible: a farmer goes
to look at a leaf and comes back forty minutes later, or loses signal in
the field (§9). Whatever holds the conversation has to outlast that gap.

Two shapes were possible.

In the first, one function runs the whole conversation and stops at
`input()` whenever it needs an answer — a phone call. The conversation
exists only in that function's local variables, and only while it runs.
A dropped connection ends it, and nothing can be saved, because nothing
exists outside the running call.

In the second, a function receives the conversation so far and one new
message, returns a reply and the conversation brought up to date, and
ends — text messages. Between two messages nothing runs. The conversation
exists only as a record, which can be kept anywhere and resumed an hour
later.

Every caller the supervisor will have is of the second kind. A web
request (FastAPI, checkpoint 9), a phone client, LangGraph's
checkpointing (§9): each hands over one message and needs an answer
back, and none of them can hold a function that waits forty minutes.
The test suite is of that kind too.

## Decision
The supervisor takes the state and one message, and returns a reply and
the new state:

    (state, message)  ->  (reply, state)

It keeps nothing between calls. The CLI is the only code that waits for
a keyboard: a loop of a few lines that reads a line, hands it to the
supervisor with the state, prints the reply and keeps the state it gets
back.

**The state holds what happened, and nothing derived from it.** What
came from outside our own code is recorded: the crop, the starting
weights the risk worker returned when the conversation began, every
question asked with the answer it got, and the question now awaiting an
answer. What our code computes from those is computed again on every
message: the causes still standing, what each answer eliminated, the
next question, and whether to stop.

The picture that settled it is correspondence chess. The players send
each other moves, not the board, and each keeps the list of moves
played. The board can always be set up again from the list; the list
cannot be recovered from the board.

The pending question is recorded because it is a move the system has
already made. The answer that arrives next can only be read against it.

The starting weights are recorded rather than requested again, although
in the skeleton they are a constant. Once the risk worker reads live
weather, a second call halfway through a conversation can return
something different, and a conversation has to reason from the weights
it started with.

Rejected:

- **The first shape.** It is the one that gets written first, because it
  reads top to bottom like the conversation itself. It fails every
  caller except a terminal, and a test can drive it only by faking the
  keyboard.
- **Storing derived values beside the moves** — the surviving
  candidates, say, next to the answers that produced them. Two records
  of one fact, which can disagree, and "don't store what you can derive"
  (§2) exists for exactly that. The saving would be nothing worth
  having: recomputing four causes, or fifty, is instant. It is the split
  `0013` drew for `Field`, recorded values against derived ones, applied
  to a conversation.

## Consequences
**Everything the narrowing loop remembers has to be in the state**,
because nothing else exists between two messages. A value kept anywhere
else — a module-level variable, an attribute on an object that outlives
a call — is a bug under this decision, and it will look like one only
when two conversations run side by side, or one is resumed.

**The shape of the state survives checkpoint 2.** Today an answer
eliminates causes; there it will update probabilities. The list of moves
stays as it is and only what is computed from it changes — the same
game, analysed again by a stronger engine.

**Keeping logic out of the CLI (§18) stops being a matter of
discipline.** The CLI has nothing to hold but the state and nothing to
do but pass it along. FastAPI at checkpoint 9 does what the CLI does,
with a request in place of the keyboard.

**In the skeleton the state lives in memory**, so a closed terminal
still loses the conversation. What changes is that the state is now one
value that could be saved, where under the first shape there was
nothing to save. Saving it is decided when a conversation is first
stored, not here.

**A conversation can be tested without a keyboard**: a test hands the
supervisor one message at a time and inspects the state after each.

**Revisit triggers:**
- **The model starts reading the farmer's answers.** A move then has to
  keep both what the farmer wrote and what the model read it as.
  Reading the text again on every message would not give the same
  reading twice: the model's reading is something that happened, not
  something to recompute.
- **LangGraph arrives.** Keeping the state between calls becomes its
  checkpointing's job. The supervisor's shape is the one that
  checkpointing works with: a state saved between calls, handed in,
  updated and handed back.
- **The conversation needs to remember something that is not a move** —
  a photo, an observation date, a forecast fetched halfway through. The
  state gains it, and the line between recorded and derived is drawn
  again for it.
