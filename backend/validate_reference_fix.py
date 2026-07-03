#!/usr/bin/env python3
"""Validate the reference-based (batch-independent) scoring against the
original batch-dependent approach, using the held-out labeled test sets
(rand_test.fa / recep_test.fa — 137 CPP + 137 non-CPP peptides each,
never seen during training).

Reports accuracy for:
  1. OLD approach, scored as one large batch (274 peptides at once) —
     this is the *best case* for the old approach, since categorise()
     has plenty of peptides to bin against. Scoring smaller batches with
     the old approach would look worse than this.
  2. OLD approach, scored one peptide at a time — the *worst case*,
     and the realistic scenario for a web form where people paste in
     just one or two sequences at a time.
  3. NEW reference-based approach, scored one at a time — should be
     identical no matter the batch size, so this number IS the
     one-at-a-time AND the whole-batch number.

Run from backend/: python validate_reference_fix.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from wlvcpp.parse import from_fasta
from wlvcpp.features import (
    datset_builder, add_corr, engineer, engineer_with_reference,
)
from wlvcpp.constants import CLASSIFIERS
from wlvcpp.predict import predict_peptides
import joblib

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')


def load_test_set(name):
    fasta_path = os.path.join(DATA_DIR, f'{name}_test.fa')
    cpps, ncpps = from_fasta(fasta_path)
    peps = cpps + ncpps
    labels = [1] * len(cpps) + [0] * len(ncpps)
    return peps, labels


def old_batch_predict(peps):
    """Mirrors the ORIGINAL calc_predictions(): S0 built once, reused (and
    progressively mutated) across both classifiers, engineer() rebinning
    against whatever's in `peps`."""
    S0 = datset_builder(peps, [])
    preds_per_classifier = []
    for name, cfg in CLASSIFIERS.items():
        S0 = add_corr(S0, cfg['adds'], cfg['subs'])
        S0 = engineer(S0, 0.9)
        S = S0[cfg['feats']]
        model = joblib.load(os.path.join(MODELS_DIR, f'{name}_model.joblib'))
        pred = model.predict_proba(S)[:, 1]
        preds_per_classifier.append(pred)
    L = len(peps)
    return [
        sum(preds_per_classifier[m][i] for m in range(len(preds_per_classifier))) / 2
        for i in range(L)
    ]


def accuracy(probas, labels):
    correct = sum(1 for p, y in zip(probas, labels) if (p >= 0.5) == bool(y))
    return correct / len(labels)


import random


def evaluate(name, single_sample_size=40):
    peps, labels = load_test_set(name)
    print(f'\n=== {name}_test.fa ({len(peps)} peptides) ===')

    # 1. OLD approach, whole batch at once (best case for old approach)
    probas_old_batch = old_batch_predict(peps)
    acc_old_batch = accuracy(probas_old_batch, labels)
    print(f'OLD, scored as one {len(peps)}-peptide batch:  {acc_old_batch:.3%}')

    # 2. OLD approach, one peptide at a time — expensive (full feature build
    # per single peptide), so evaluate on a random subsample for speed.
    rng = random.Random(43)
    idx = rng.sample(range(len(peps)), min(single_sample_size, len(peps)))
    sample_peps = [peps[i] for i in idx]
    sample_labels = [labels[i] for i in idx]
    probas_old_single = [old_batch_predict([p])[0] for p in sample_peps]
    acc_old_single = accuracy(probas_old_single, sample_labels)
    print(f'OLD, scored one at a time ({len(idx)}-peptide sample): {acc_old_single:.3%}')

    # 3. NEW reference-based approach, whole batch (== any batch size, by design)
    dummy_names = [f'p{i}' for i in range(len(peps))]
    results_new = predict_peptides(dummy_names, peps)
    probas_new = [r['probability'] for r in results_new]
    acc_new = accuracy(probas_new, labels)
    print(f'NEW, reference-based (batch-independent):     {acc_new:.3%}')

    # NEW on the same subsample, to compare apples-to-apples with OLD-single
    acc_new_sample = accuracy([probas_new[i] for i in idx], sample_labels)
    print(f'NEW, same {len(idx)}-peptide sample:                  {acc_new_sample:.3%}')

    # sanity: NEW one-at-a-time should match NEW whole-batch exactly
    check_idx = idx[:5]
    matches = all(
        abs(predict_peptides(['x'], [peps[i]])[0]['probability'] - probas_new[i]) < 1e-9
        for i in check_idx
    )
    print(f'NEW batch-independence check (5 samples match individually): {matches}')

    return acc_old_batch, acc_old_single, acc_new


if __name__ == '__main__':
    print('Validating reference-based scoring against held-out labeled test sets.')
    print('These 274 peptides per classifier were NOT used in training.\n')
    r_old_batch, r_old_single, r_new = evaluate('rand')
    c_old_batch, c_old_single, c_new = evaluate('recep')

    print('\n=== Summary (combined mean-of-two-classifiers accuracy per test set) ===')
    print(f'{"":40s} {"rand_test":>12s} {"recep_test":>12s}')
    print(f'{"OLD, whole-batch (best case)":40s} {r_old_batch:>12.3%} {c_old_batch:>12.3%}')
    print(f'{"OLD, one-at-a-time (realistic)":40s} {r_old_single:>12.3%} {c_old_single:>12.3%}')
    print(f'{"NEW, reference-based":40s} {r_new:>12.3%} {c_new:>12.3%}')
