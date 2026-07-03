"""Smoke tests for the prediction pipeline.

These aren't a full validation suite (that would mean re-running against
rand_test.fa / recep_test.fa properly) — they're a fast sanity check for CI:
does the pipeline run end-to-end, and does it still call well-known
reference peptides correctly. Run with: pytest backend/tests
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from wlvcpp.predict import predict_peptides
from wlvcpp.parse import check_entries

# TAT peptide (HIV-1) — a textbook, well-established cell-penetrating peptide.
KNOWN_CPP = "GRKKRRQRRRPPQ"
# A generic, non-cationic sequence with no known CPP activity.
KNOWN_NON_CPP = "DEEDEEDEEDEE"


def test_check_entries_parses_basic_fasta():
    lines = [">pep1", KNOWN_CPP, ">pep2", KNOWN_NON_CPP]
    names, peps, discarded = check_entries(lines)
    assert names == ["pep1", "pep2"]
    assert peps == [KNOWN_CPP, KNOWN_NON_CPP]
    assert discarded == []


def test_check_entries_discards_non_alphabetic_and_blank():
    lines = [">pep1", "AB CD", ">pep2", ""]
    names, peps, discarded = check_entries(lines)
    assert peps == []
    assert len(discarded) == 2


def test_predict_peptides_runs_and_returns_expected_shape():
    results = predict_peptides(["tat", "acidic"], [KNOWN_CPP, KNOWN_NON_CPP])
    assert len(results) == 2
    for r in results:
        assert set(r.keys()) == {"name", "peptide", "predicted_class", "probability"}
        assert 0.0 <= r["probability"] <= 1.0
        assert r["predicted_class"] in ("CPP", "non-CPP")


def test_known_cpp_scores_above_threshold():
    """Regression guard: the textbook TAT peptide should score as CPP.
    If this starts failing, something in the feature pipeline or models broke."""
    results = predict_peptides(["tat"], [KNOWN_CPP])
    assert results[0]["predicted_class"] == "CPP"
    assert results[0]["probability"] >= 0.5


def test_empty_input_returns_empty_list():
    assert predict_peptides([], []) == []


def test_scores_are_batch_independent():
    """Regression guard for the bug found in production: the original
    algorithm rebinned features against whatever else was in the same
    request, so the same peptide could score very differently depending
    on batch composition (demonstrated: TAT scored 84.2% alone vs 98.3%
    alongside penetratin). This must no longer be true."""
    tat = "GRKKRRQRRRPPQ"
    penetratin = "RQIKIWFQNRRMKWKK"

    alone = predict_peptides(["tat"], [tat])[0]["probability"]
    with_penetratin = predict_peptides(["tat", "pen"], [tat, penetratin])[0]["probability"]
    with_ten_others = predict_peptides(
        ["tat"] + [f"junk{i}" for i in range(10)],
        [tat] + ["ACDEFGHIKLMNPQRSTVWY"[i % 20:] + "AAA" for i in range(10)],
    )[0]["probability"]

    assert alone == with_penetratin == with_ten_others
