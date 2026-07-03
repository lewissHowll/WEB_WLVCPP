"""Prediction pipeline: loads the two pretrained SVMs and scores new peptides.

Batch-independent scoring: each classifier gets its own freshly-built
feature dataframe, binned against FIXED reference stats learned once from
the training data (see train_models.py / fit_reference_stats). This
replaces two issues present in the original script's calc_predictions():

1. The original bins each query peptide's features into deciles based on
   quantiles of *whatever else is in the same request* — so the same
   peptide could score very differently depending on what else you
   submitted alongside it (demonstrated: TAT peptide alone scored 84.2%,
   but 98.3% when submitted with penetratin). Reference-based binning
   fixes this: a peptide's score no longer depends on batch composition.
2. The original also reused and progressively re-transformed the same
   dataframe across both classifiers instead of rebuilding it fresh per
   classifier (mirroring how training data IS rebuilt fresh each time).
   Building S0 fresh per classifier here fixes that too.

This changes prediction outputs from the original script — see
docs/reference_validation.md for accuracy comparison against
rand_test.fa / recep_test.fa before trusting this over the original.
"""
import os
from typing import List, TypedDict

import joblib

from .features import datset_builder, add_corr, engineer_with_reference, AA2GROUP
from .constants import CLASSIFIERS

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')

_models = {}
_ref_stats = {}


def _load_models():
    if not _models:
        for name in CLASSIFIERS:
            model_path = os.path.join(MODELS_DIR, f'{name}_model.joblib')
            ref_path = os.path.join(MODELS_DIR, f'{name}_refstats.joblib')
            if not os.path.exists(model_path) or not os.path.exists(ref_path):
                raise FileNotFoundError(
                    f"Model/reference-stats files missing for '{name}'. "
                    "Run train_models.py first."
                )
            _models[name] = joblib.load(model_path)
            _ref_stats[name] = joblib.load(ref_path)
    return _models, _ref_stats


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

    models, ref_stats = _load_models()
    L = len(peps)

    preds_per_classifier = []
    for name, cfg in CLASSIFIERS.items():
        S0 = datset_builder(peps, [])  # fresh build, not reused across classifiers
        S0 = add_corr(S0, cfg['adds'], cfg['subs'])
        S0 = engineer_with_reference(S0, ref_stats[name])
        S = S0[cfg['feats']]
        pred = models[name].predict_proba(S)[:, 1]
        preds_per_classifier.append(pred)

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
