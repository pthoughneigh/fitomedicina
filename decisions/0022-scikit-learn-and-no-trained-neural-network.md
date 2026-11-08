# 0022 — scikit-learn does the fitting, and no neural network is trained

**Date:** 2026-11-08
**Status:** accepted

## Context
§8 planned three depths of "implement": eight to ten techniques written
out in NumPy (Tier 1), about thirty called from a library and evaluated
honestly (Tier 2), and the rest tried and rejected (Tier 3). Six of the
seven unsupervised methods were to be rebuilt in NumPy as well, §18 had
cosine similarity "written by hand and never imported", and §11 listed
a from-scratch version beside the library call among the things that
make the repository read as real work. All of it assumed that this
project was where the mathematics would be learned.

It no longer is. Writing the methods out, in NumPy and pandas with
scikit-learn beside them, now happens in a separate project, and neural
networks will get a project of their own once they are learned. This
one is for the agent system and for a product people use (`0021`). Two
things had to be settled: what this project uses instead, and where the
line falls between calling a library and writing code.

§9 also had PyTorch and `timm` for vision, in months four to five: a
pretrained backbone fine-tuned to triage photos of leaves.

## Decision
**Whatever is fitted, tuned or evaluated comes from scikit-learn:**

- the models themselves, with their preprocessing and pipelines;
- cross-validation, including the splits by year that CY-Bench requires
  (§6): `LeaveOneGroupOut`, with the year as the group;
- the metrics of §8 and the plots of §9: `roc_curve`,
  `confusion_matrix`, `calibration_curve`, and the `RocCurveDisplay`,
  `ConfusionMatrixDisplay` and `CalibrationDisplay` that draw them in
  the notebooks;
- `PCA`, `KMeans`, `DBSCAN` and the rest, when the comparison worker
  arrives;
- `cosine_similarity`, in the reranking.

NumPy and pandas are used wherever data is loaded, joined, cleaned and
turned into features: BonaRes's forty or so tables, growing degree
days, leaf wetness hours. That is data work, not a reimplementation of
a method.

The picture is a radiologist, who does not build the scanner. Her skill
is choosing the scan that answers the question and reading it honestly,
including what it cannot show. Here that skill shows in the choices and
in the evaluation: a split that does not leak, a confusion matrix
priced by what each error costs (§8), a calibration curve.

**§8's three tiers become two.** Tier 1 is withdrawn. Tier 2 is the
default, and Tier 3 stays, because a loser with a written explanation
is where judgement shows (§8).

**Gradient boosting starts with scikit-learn's
`HistGradientBoostingClassifier` and `HistGradientBoostingRegressor`.**
XGBoost and CatBoost enter as challengers on the same splits, and only
if they win, measured. Otherwise they stay in the writeup as Tier 3
losers. §9's case for CatBoost was ordered target encoding for
high-cardinality categoricals. scikit-learn's `TargetEncoder`
cross-fits its encoding, so that a row's own target does not leak into
it, which is the problem CatBoost's ordering solves; and
`HistGradientBoosting` takes categoricals directly. Whatever CatBoost
adds beyond that, it has to show on our data. Tuning follows the same
rule: `RandomizedSearchCV` first, and Optuna only if it finds better
settings within the small budget §9 set.

**No neural network is trained, fine-tuned or run on our own servers.**
PyTorch and `timm` leave §9, and scikit-learn's own neural network,
`MLPClassifier`, is left out as well. Photos remain what §7 and §12
made them, triage and not diagnosis, but the triage goes to the
multimodal model the system already calls. It says what is visible and
whether it is worth escalating, and it does not name a cause: naming
causes is the loop's work (§3). §9 already asked for exactly this to be
tried before anything custom was built. The LLM and the embedding model
are neural networks, used as services through an API. They are the
agent half of this project, not an exception to the rule.

**One exception: the narrowing loop's own arithmetic.** The posterior
over the knowledge table and the information gain of each question
(§8) are not a model fitted to data. They are reasoning over a table we
wrote, and scikit-learn has no method for that. The nearest is
`mutual_info_score`, which takes two arrays of labels or a contingency
table of counts. Measured on 8 November with scikit-learn 1.9.1: given
a table of probabilities it raised `ValueError: math domain error`, and
the same table scaled up to counts gave the value computed by hand. So
the loop uses `scipy.stats.entropy` and a few lines of NumPy.

Rejected:

- **Keeping Tier 1.** The learning it was for now happens elsewhere,
  and here it would take the months the agent half needs. §8 already
  warned that doing everything from scratch is "reimplement
  scikit-learn", a different project.
- **`mutual_info_score` on probabilities scaled into counts.** It gives
  the right number, and leaves the reader wondering what the factor of
  a thousand is for. A function used against its meaning is a
  workaround, not use of the library.
- **XGBoost and CatBoost by default**, as §9 had them. Two more
  dependencies, before anything has shown that scikit-learn's own
  boosting is not enough.
- **Fine-tuning a vision model**, as §9 had it. It is the neural
  network this project no longer trains, and §12 had already kept
  photos out of the headline: an incumbent with 120 million labelled
  images (§7) cannot be caught.

## Consequences
**§8's Tier 1 list resolves item by item:**

- entropy and mutual information: the exception above;
- Naive Bayes: the posterior over our own table is the exception, and
  a Naive Bayes fitted to data is scikit-learn's;
- a small decision tree: `DecisionTreeClassifier(criterion="entropy")`,
  the loop's own criterion, so the connection §8 wanted survives;
- gradient descent and SGD: inside scikit-learn's estimators, never by
  hand;
- gradient boosting: `HistGradientBoosting`, as above;
- logistic regression: `LogisticRegression`, whose coefficients still
  become the odds ratios explained to a farmer (§8);
- cosine similarity: `cosine_similarity`;
- the six unsupervised methods Tier 1 was to rebuild: scikit-learn,
  with the comparison worker, after the launch (`0021`).

**The posterior stays the loop's when the table is learned.** Once the
season log holds labelled cases, the table's numbers can be fitted
instead of written. `CategoricalNB` learns a table of exactly this
shape, a log-probability for every cause and every answer to every
question. But it predicts only from a full row of answers: with one
question unanswered it raises `Input X contains NaN` (measured, 1.9.1),
and a farmer answers three questions of eight (§8). So scikit-learn
fits the table and the loop applies it to the questions actually
answered.

**SciPy is declared in `pyproject.toml` by the first module that
imports it**, although scikit-learn already brings it. A library our
own code imports is one we name, so that our code does not break on
the day scikit-learn stops needing it.

**§12's reason for Python 3.13 loses its binding constraint**,
CatBoost's wheels. 3.13 stays: nothing argues for moving, and
scikit-learn 1.9.1 installs and runs on it (measured, 3.13.16).

**§2, §8, §9, §11, §12 and §18 are amended accordingly** where they say
otherwise: the from-scratch tiers and the rebuild of the unsupervised
methods, the hand-written cosine similarity, the default boosting
libraries, PyTorch, and the fine-tuned backbone.

**Revisit triggers:**
- **The loop's arithmetic outgrows a few lines**, or scikit-learn gains
  a method for information gain over a table of probabilities. The
  exception is weighed again.
- **The farmer half needs a method scikit-learn does not have.** It
  comes from the library that has it, and a record says why
  scikit-learn was not enough.
- **A job that only a neural network of our own can do**: photo triage
  through the multimodal model failing its eval, say. That takes a new
  record, written once neural networks have been learned in their own
  project, not an exception to this one.
