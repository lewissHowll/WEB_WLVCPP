"""Prediction pipeline: loads the two pretrained SVMs and scores new peptides.

IMPORTANT — faithfully mirrors the original script's scoring order:
the same `S0` dataframe is passed through `add_corr` + `engineer` for the
'rand' classifier THEN reused (already transformed) for the 'recep'
classifier, exactly as the original `calc_predictions()` did. This wasn't
changed because the published feature sets (FEATS_RAND / FEATS_RECEP) were
selected/validated against this exact behaviour — silently "fixing" it would
change prediction outputs in a way that hasn't been re-validated against
rand_test.fa / recep_test.fa. See README for more on this.
"""
import os
from typing import List, TypedDict

import joblib
import pandas as pd

from .features import datset_builder, engineer, add_corr, AA2GROUP
from .constants import CLASSIFIERS

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')

_models = {}


def _load_models():
    if not _models:
        for name in CLASSIFIERS:
            path = os.path.join(MODELS_DIR, f'{name}_model.joblib')
            if not os.path.exists(path):
                raise FileNotFoundError(
                    f"Model file missing: {path}. Run train_models.py first."
                )
            _models[name] = joblib.load(path)
    return _models


class Prediction(TypedDict):
    name: str
    peptide: str
    predicted_class: str
    probability: float


def residue_groups(peptide: str) -> List[str]:
    """Group label per residue, for the frontend's colour-coded strip.
    Unknown/ambiguous residues (X,B,J,Z,U) map to '' (no group)."""
    return [AA2GROUP.get(r.upper(), '') for r in peptide]


def predict_peptides(names: List[str], peps: List[str]) -> List[Prediction]:
    if not peps:
        return []

    models = _load_models()
    S0 = datset_builder(peps, [])

    preds_per_classifier = []
    for name, cfg in CLASSIFIERS.items():
        S0 = add_corr(S0, cfg['adds'], cfg['subs'])
        S0 = engineer(S0, 0.9)
        S = S0[cfg['feats']]
        pred = models[name].predict_proba(S)[:, 1]
        preds_per_classifier.append(pred)

    L = len(peps)
    probas = [
        sum(preds_per_classifier[m][i] for m in range(len(preds_per_classifier)))
        / len(preds_per_classifier)
        for i in range(L)
    ]

    results: List[Prediction] = []
    for i in range(L):
        results.append({
            'name': names[i],
            'peptide': peps[i],
            'predicted_class': 'CPP' if probas[i] >= 0.5 else 'non-CPP',
            'probability': round(float(probas[i]), 4),
        })
    return results
