#!/usr/bin/env python3
"""Train the two WLVCPP SVM classifiers ONCE and pickle them to models/.

Run this whenever rand_train.fa / recep_train.fa change. The API
(wlvcpp/predict.py) just loads the pickled models — it never retrains
per-request, which is what made the original CLI script slow (~8s per run
even for a handful of peptides).

Usage:
    python train_models.py
"""
import os
import joblib
from sklearn.svm import SVC

from wlvcpp.parse import from_fasta
from wlvcpp.features import datset_builder, engineer
from wlvcpp.constants import CLASSIFIERS

SEED = 43
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')


def train_one(name: str, cfg: dict) -> None:
    fasta_path = os.path.join(DATA_DIR, cfg['train_fasta'])
    cpps, ncpps = from_fasta(fasta_path)
    data = datset_builder(cpps, ncpps)
    data = features_add_corr_and_engineer(data, cfg)
    y = data['cpp']
    X = data[cfg['feats']]

    model = SVC(max_iter=10000, probability=True, random_state=SEED)
    model.fit(X, y)

    out_path = os.path.join(MODELS_DIR, f'{name}_model.joblib')
    joblib.dump(model, out_path)
    print(f'[{name}] trained on {len(cpps)} CPP / {len(ncpps)} non-CPP peptides '
          f'-> {out_path}')


def features_add_corr_and_engineer(data, cfg):
    from wlvcpp.features import add_corr
    data = add_corr(data, cfg['adds'], cfg['subs'])
    data = engineer(data, 0.9)
    return data


def main() -> None:
    os.makedirs(MODELS_DIR, exist_ok=True)
    for name, cfg in CLASSIFIERS.items():
        train_one(name, cfg)
    print('\nDone. Commit the .joblib files in models/ (or run this in your build step).')


if __name__ == '__main__':
    main()
