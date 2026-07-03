# Reference-based scoring: what changed and why

## The problem

The original `WLVCPP.py`'s `categorise()` function bins each numeric feature
into deciles (0.1–1.0) using the **quantiles of whatever peptides are in the
current batch**:

```python
mn, mx = min(vals), max(vals)
d = (mx - mn) / 10
# ... value gets bucketed into (val - mn) / d, rounded up to nearest tenth
```

This is fine for the *training* data, where "the batch" is the fixed
train_.fa file. But `calc_predictions()` applies the exact same function to
the **query peptides** — so a peptide's feature values, and therefore its
score, depend on what else was submitted alongside it in the same request.

With a single peptide this is degenerate: `min == max` for every column
(there's only one data point), so the bucket width `d = 0`, and **every
feature collapses to exactly `0.1`** regardless of the peptide's actual
composition. The SVM ends up scoring an almost-constant, near-meaningless
input vector.

### Demonstrated impact

Submitting the TAT peptide (`GRKKRRQRRRPPQ`) alone vs. alongside penetratin:

| Submission | TAT probability |
|---|---|
| TAT alone | 84.2% |
| TAT + penetratin | 98.3% |
| TAT + penetratin + 10 random junk peptides | 99.5% |

Same peptide, three different scores, purely as a function of request
composition — nothing to do with the peptide itself.

## The fix

`fit_reference_stats()` (in `wlvcpp/features.py`) learns the decile bucket
boundaries **once, from the training data**, at `train_models.py` time, and
saves them (`models/{name}_refstats.joblib`). `engineer_with_reference()`
applies those *fixed* boundaries to any query batch, instead of recomputing
them from the query itself. A peptide's score no longer depends on what
else is in the request — verified by `tests/test_predict.py::
test_scores_are_batch_independent`.

This also fixes a second, smaller issue: the original reused and
progressively re-transformed the same dataframe across the `rand` and
`recep` classifiers instead of rebuilding it fresh for each (the way
training data is rebuilt fresh each time). Each classifier now gets its own
fresh feature build, mirroring how training works.

## Validation against held-out test data

`rand_test.fa` / `recep_test.fa` (137 CPP + 137 non-CPP peptides each, not
used in training) were scored three ways — see
`backend/validate_reference_fix.py` to reproduce:

| | rand_test.fa | recep_test.fa |
|---|---|---|
| **OLD**, scored as one 274-peptide batch (best case for the old method) | 89.1% | 81.4% |
| **OLD**, scored one peptide at a time (realistic web-form usage — 40-peptide sample) | 57.5% | 57.5% |
| **NEW**, reference-based (identical regardless of batch size) | 90.9% | 82.5% |

Two things stand out:

1. **One-at-a-time accuracy with the old method is barely above chance
   (57.5%, vs. 50% for a coin flip)** — this is the realistic case for
   anyone pasting one or two sequences into a web form, which is most of
   how this tool will actually get used.
2. The new method isn't just more *consistent* — it's also slightly more
   *accurate* even in the old method's best-case (whole-batch) scenario
   (90.9% vs 89.1%, 82.5% vs 81.4%), likely because fixed bucket boundaries
   learned from 410+410 training peptides are more stable than boundaries
   re-estimated from a handful of quantile points in a small query batch.

### Confirmed against the original, unmodified script

Both issues below were verified by running the researcher's own
`WLVCPP.py` directly — not this app's refactored code — with only the
one-line syntax fix needed to make it execute at all (the stray URL
pasted into `from_fasta()`, unrelated to either bug).

**Batch-dependent scoring.** Three different single peptides, each run
through the original script alone:

```
tat     (GRKKRRQRRRPPQ)   -> 0.842571
junk    (AAAAAAAAAA)      -> 0.840178
acidic  (DEEDEEDEEDEE)    -> 0.848713
```

All near-identical despite being very different peptides (one cationic
CPP-like, one all-alanine, one acidic) — consistent with every feature
collapsing to the same constant `0.1` regardless of sequence, as described
above.

**Run-to-run instability, on top of that.** The *exact same* peptide, run
through the *exact same, unmodified* script twice in a row:

```
Run 1: tat   CPP   0.848759
Run 2: tat   CPP   0.838910
```

Same input, same code, back to back — different answers. This is a
separate bug: the original script retrains both SVMs from scratch on
every invocation (`SVC(max_iter=10000, probability=True)`, no
`random_state` set), and scikit-learn's probability calibration (Platt
scaling) uses a randomized internal cross-validation split unless the
seed is pinned. Every fresh training run lands on a slightly different
model.

This app's version doesn't have this second issue — models are trained
once with a fixed `random_state` and pickled — but that fix was made for
performance reasons (avoiding retraining on every web request), before
the batch-dependence issue was found. It's a useful data point for the
researcher conversation regardless: single-peptide scores from the
original tool weren't just uninformative, they were also unreproducible
run to run, which is a stronger indicator this was an oversight rather
than an intentional design choice.

## What this means for the published feature sets

`FEATS_RAND` / `FEATS_RECEP` and the `adds`/`subs` correlation-feature lists
in `wlvcpp/constants.py` were presumably selected during the original
research using the batch-dependent scoring method (i.e. selected on data run
through `categorise()` batch-by-batch, or possibly through some other
process — worth asking). It's possible a fresh feature-selection pass under
the reference-based method would settle on the same features (accuracy
above suggests they still work well), but that hasn't been re-derived —
this fix reuses the original researcher's feature selections as-is and only
changes *how each feature value gets computed* for query peptides, not
*which* features are used.
