#!/usr/bin/env python3
"""Train the two WLVCPP SVM classifiers ONCE and pickle them to models/.

Run this whenever rand_train.fa / recep_train.fa change. The API
(wlvcpp/predict.py) just loads the pickled models — it never retrains
per-request, which is what made the original CLI script slow (~8s per run
even for a handful of peptides).

This also fits and saves *reference feature stats* per classifier
(fit_reference_stats in wlvcpp/features.py) — the fixed decile-bucket
boundaries learned from the training data, which predict.py then applies
to query peptides instead of rebinning against whatever else happens to
be in the same request. See README's "Batch-independent scoring" section
for why this matters.

Usage:
    python train_models.py
"""
import os
import joblib
from sklearn.svm import SVC

from wlvcpp.parse import from_fasta
from wlvcpp.features import datset_builder, add_corr, fit_reference_stats, engineer_with_reference
from wlvcpp.constants import CLASSIFIERS

SEED = 43
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')


def train_one(name: str, cfg: dict) -> None:
    fasta_path = os.path.join(DATA_DIR, cfg['train_fasta'])
    cpps, ncpps = from_fasta(fasta_path)
    data = datset_builder(cpps, ncpps)
    data = add_corr(data, cfg['adds'], cfg['subs'])

    # Learn fixed bucket boundaries from the training data itself, ONCE.
    ref_stats = fit_reference_stats(data)
    data = engineer_with_reference(data, ref_stats)

    y = data['cpp']
    X = data[cfg['feats']]

    model = SVC(max_iter=10000, probability=True, random_state=SEED)
    model.fit(X, y)

    model_path = os.path.join(MODELS_DIR, f'{name}_model.joblib')
    ref_path = os.path.join(MODELS_DIR, f'{name}_refstats.joblib')
    joblib.dump(model, model_path)
    joblib.dump(ref_stats, ref_path)
    print(f'[{name}] trained on {len(cpps)} CPP / {len(ncpps)} non-CPP peptides '
          f'-> {model_path}\n         reference stats -> {ref_path}')


def main() -> None:
    os.makedirs(MODELS_DIR, exist_ok=True)
    for name, cfg in CLASSIFIERS.items():
        train_one(name, cfg)
    print('\nDone. Commit the .joblib files in models/ (or run this in your build step).')


if __name__ == '__main__':
    main()
