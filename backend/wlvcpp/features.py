"""Peptide descriptor / feature engineering, ported unchanged from WLVCPP.py.

The math and logic here are the researcher's original algorithm — only
reorganised into a module and typed. Do not change behaviour without
re-validating against rand_test.fa / recep_test.fa.
"""
from typing import Dict, List
import numpy as np
import pandas as pd

pd.options.mode.chained_assignment = None  # default='warn'

MPS: List[str] = ['A', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L', 'M', 'N',
                   'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'Y']

AAGROUPS: Dict[str, List[str]] = {
    'pol': ['S', 'T', 'C', 'P', 'N', 'Q'],
    'non': ['G', 'A', 'V', 'L', 'I', 'M'],
    'aro': ['F', 'Y', 'W'],
    'pos': ['K', 'R', 'H'],
    'neg': ['D', 'E'],
}

AA2GROUP: Dict[str, str] = {a: g for g in AAGROUPS for a in MPS if a in AAGROUPS[g]}


def categorise(data: pd.DataFrame) -> pd.DataFrame:
    """Bin numeric columns into deciles after IQR-based outlier clipping."""
    for c in data.columns:
        if c in ('cpp', 'peps'):
            continue
        q1 = data[c].quantile(0.25)
        q3 = data[c].quantile(0.75)
        iqr = q3 - q1
        low = q1 - 1.5 * iqr
        up = q3 + 1.5 * iqr
        vals = list(data[c])
        for i in range(len(vals)):
            if vals[i] > up:
                vals[i] = up
            elif vals[i] < low:
                vals[i] = low
        mn, mx = min(vals), max(vals)
        d = (mx - mn) / 10
        for j in range(len(vals)):
            for i in range(1, 11):
                if vals[j] <= mn + i * d:
                    vals[j] = i / 10
                    break
        data[c] = vals
    return data


def datset_builder(cpps: List[str], ncpps: List[str]) -> pd.DataFrame:
    """Build the full descriptor table: AA composition, group composition,
    dipeptide-group composition, AA pairwise sum/diff ratios, length."""
    peptides = cpps + ncpps
    peptides = [p.upper() for p in peptides]
    arap = [i + '+' + j for i in MPS for j in MPS if i < j]
    aran = [i + '-' + j for i in MPS for j in MPS if i < j]

    data: Dict[str, List[float]] = {c: [] for c in MPS + aran + arap}
    for c in AAGROUPS:
        data[c] = []

    # amino acid composition
    for c in MPS:
        for p in peptides:
            data[c].append(p.count(c))

    # physicochemical group composition
    for c in AAGROUPS:
        g = AAGROUPS[c]
        for p in peptides:
            data[c].append(len([r for r in p if r in g]))

    # dipeptide-group composition
    dpgroups: List[str] = []
    for i in AAGROUPS:
        for j in AAGROUPS:
            f, s = sorted([i, j])
            g = f + '_' + s
            if g not in dpgroups:
                dpgroups.append(g)

    dipeps = {g: [] for g in dpgroups}
    for ij in dpgroups:
        i, j = ij.split('_')
        for p in peptides:
            L = len(p)
            dplist = [
                AA2GROUP[p[a]] + '_' + AA2GROUP[p[a + 1]]
                for a in range(L - 1)
                if not any(b in (p[a], p[a + 1]) for b in ('X', 'B', 'J', 'Z', 'U'))
            ]
            k = dplist.count(ij)
            if i != j:
                k += dplist.count(j + '_' + i)
            dipeps[i + '_' + j].append(k)
    dipeps_df = pd.DataFrame(dipeps)

    # pairwise AA sum/diff ratios
    for i in MPS:
        for j in MPS:
            if i < j:
                for p in peptides:
                    data[i + '+' + j].append(abs(p.count(i) + p.count(j)))
                    data[i + '-' + j].append(abs(p.count(i) - p.count(j)))

    data['length'] = []
    data['peps'] = []
    for p in peptides:
        data['peps'].append(p)
        data['length'].append(len(p))

    if ncpps:
        data['cpp'] = [1 if p in cpps else 0 for p in peptides]

    df = pd.DataFrame(data)
    for c in dipeps_df:
        df[c] = dipeps_df[c]
    return df


def engineer(data: pd.DataFrame, thr: float) -> pd.DataFrame:
    for c in data.columns:
        if c in ('cpp', 'peps'):
            continue
        minv = min(data[c])
        data[c] = np.log1p(data[c] - minv + 1)
        data[c] = categorise(pd.DataFrame(data[c]))
    return data


def add_corr(data: pd.DataFrame, adds: List[str], subs: List[str]) -> pd.DataFrame:
    data['corr'] = round(sum(data[c] for c in adds) - sum(data[c] for c in subs))
    return data
