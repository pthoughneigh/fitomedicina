# 0023 — Paprika alone until the launch, and the agent work first

**Date:** 2026-11-14
**Status:** accepted

## Context
§7 made winter wheat the training ground and paprika the product: wheat
first, because CY-Bench and BonaRes hold data for it and results can be
checked against published benchmarks, and paprika around month four, to
show that a new crop is absorbed in a week. `0021` kept that order up to
the launch: the real loop (2), live data (3), the first trained model
(4), persistence (5), paprika (6) and the evidence worker (7), then the
launch (9), then analytics (8). §18 put CI and the model, the first fake
replaced, between checkpoints 1 and 2, and left LangGraph to be argued
"when it arrives".

Three things have changed since. The work with CY-Bench happens in the
separate project `0022` describes, so this one would train a model on
wheat data for a crop the product no longer needs first. The first real
users are within reach: growers of paprika who can test the system, and
no grower of wheat. And the part of this project most worth having early
is the agent system and its evaluation, which `0022` made this project's
centre. In the old order much of it came last before the launch: the
evidence worker's embeddings and retrieval, and the argument for
LangGraph.

## Decision
**Paprika is the only crop until the launch.** The illustrative wheat
pack stays the skeleton's pack until checkpoint 2, where the real table
replaces it: paprika's, with a source for every rule (`0020`). Wheat,
and any other crop, comes after the launch.

**The order up to the launch is now:**

1. the rest of checkpoint 1: the supervisor, the CLI, the README, the
   tag;
2. CI;
3. the model as the reader of an answer, with the pseudonymization
   boundary and an eval run repeatedly on a golden set of answers:
   accuracy, a confusion matrix, and the cost of each error, since an
   answer read wrongly costs more than a question asked again. The
   Anthropic SDK and PydanticAI are weighed there;
4. LangGraph, argued against the supervisor that then exists: adopted
   if it wins, and otherwise rejected in a record;
5. checkpoint 2, the real loop, on paprika;
6. checkpoint 7, the evidence worker: embeddings, retrieval filtered by
   crop and country, reranking, and answers with citations, with the
   search offered to the model as a tool where one search is not
   enough. An MCP server follows it;
7. checkpoint 3, live weather and soil;
8. checkpoint 4, the reader as a classification study;
9. checkpoint 5, persistence and the season log, without the import
   layer (`0021`); treatment from the registry for paprika (`0007`);
   then checkpoint 9, the launch.

After the launch come new crops, wheat among them, which is what
checkpoint 6 now means, and then analytics (8), as `0021` set. The
numbers stay as they are, as in `0021`: they are addresses, not places
in a queue.

**Checkpoint 4 becomes the study of the reader.** Classifiers from
scikit-learn (`0022`), TF-IDF features with logistic regression or a
linear SVM to start with, are compared with the model on the golden
set. The split is by farmer, so that one person's way of answering is
never in both training and test; the threshold for "not read" is chosen
by the cost of each error; and calibration is shown and the losers are
written up. Its data can come before any app does: growers asked to
answer the pack's questions in their own words, anonymously. A reader
that runs locally is also the lever of §5: a farmer's words that never
leave the system are never transferred.

**The MCP server is a door, not a room.** Inside the system the model
has no tools to discover, and between parts of one codebase a protocol
is only cost. Outside it, MCP is a third door into the same house,
beside the CLI and the API: the evidence search, guidance from the
bulletins with citations, filtered by crop and country, and later the
registry, offered to someone else's assistant. Like the CLI, it holds
no logic.

Rejected:

- **§7's order, wheat first.** Its reason was the data for the trained
  model, and that work now happens in the other project. Here it would
  build a wheat model before paprika's table, for users the product
  will not have before the launch.
- **Both crops before the launch**, as checkpoint 6 had it. The
  research doubles, keys, bulletins and registrations for a second
  crop, for a claim that a new crop is a file and not code. A second
  crop after the launch shows that just as well, with real use behind
  it.
- **The evidence worker before checkpoint 2.** About a month sooner,
  but checkpoint 2 is the product's core, and its search for sources,
  Serbian extension material on paprika, is in good part the search
  the corpus needs. In this order it is done once.
- **A data pipeline stack: dbt, Airflow, Trino, BigQuery.** Nothing
  here has their job: a handful of tables, one database, a cache per
  grid cell. Adding them would be techniques looking for work (§8).
- **MCP inside the system**, for the reason above.

## Consequences
**Checkpoint 6's content, paprika, moves into checkpoint 2**, and
checkpoint 6 now means the second crop, after the launch. The claim of
§4, a new crop absorbed in a week, is shown after the launch.

**Both halves of the system work on one crop again**, as §7 wanted: the
risk worker's priors (3) and the trained model (4) both serve paprika,
which a model trained on wheat would not have done.

**The risk worker's priors for paprika rest on simpler rules than
wheat's would have.** Published models of disease risk driven by the
weather are fewer for pepper than for wheat, so checkpoint 3 leans on
rules from the literature, and their sources are looked for in
checkpoint 2, with the table's. Under plastic the weather outside says
less, since leaf wetness in a tunnel is not leaf wetness in the open:
the worker reads `protection` (§16), or says plainly that for a tunnel
it gives no head start.

**A test by real growers is real personal data**, even among friends.
Before the first grower uses the app, the parts of the launch gate that
concern them are in place: a privacy notice in Serbian, consent, and
what is kept and for how long (§5). Answers collected for the golden
set are anonymous, and they ask for nothing the answer does not need.
The review by a lawyer stays at checkpoint 9 (`0021`).

**The context file's §6, §7, §8, §9, §11, §12 and §18 carry a dated
note** where they say otherwise.

**Revisit triggers:**
- **A grower of another crop is ready to test before the launch.**
  Adding a crop earlier is a new file in `knowledge/`, and the order is
  weighed again.
- **The reader study finds the model and a local classifier about
  equally good.** Which one reads in production, or the classifier as
  the fallback when the model does not answer, is decided then, on the
  numbers.
- **LangGraph wins in step 4.** The supervisor's state then lives in
  its checkpointing, and that record closes `0019`'s trigger.
