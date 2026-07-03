"""Fitted feature selections for the two SVM classifiers, ported unchanged
from WLVCPP.py. These are the researcher's selected features/weights, not
values to be tuned here.
"""

FEATS_RAND = [92.91, 93.41, 93.43, -0.85, -65, 93.17, 93.17, 93.43, 93.43, 'A+L', 'A+Y', 'A-G', 'A-I', 'A-N', 'A-S', 'C+E', 'C+I', 'C+K', 'C+L', 'C+N', 'C+R', 'C+W', 'C+Y', 'C-L', 'C-P', 'D+I', 'D+Y', 'D-K', 'D-W', 'E+K', 'E+P', 'E+Y', 'E-H', 'E-V', 'F+G', 'F+K', 'F-T', 'G+R', 'G+W', 'G-L', 'G-R', 'G-S', 'H+I', 'H+M', 'H+W', 'H-Q', 'I+Q', 'I-P', 'K', 'K+N', 'K+W', 'K-L', 'L+N', 'L-R', 'L-T', 'M', 'M+R', 'M-R', 'M-V', 'N+R', 'N+T', 'N+W', 'N-P', 'N-S', 'P-Q', 'P-V', 'Q-Y', 'T-W', 'aro_aro', 'aro_neg', 'corr', 'length', 'neg_neg', 'neg_non']
ADDS_RAND = ['pos_pos', 'A', 'K', 'L', 'R', 'A-H', 'A-R', 'C-K', 'C-L', 'C-R', 'D-K', 'D-L', 'D-R', 'E-K', 'E-R', 'F-L', 'F-R', 'G-H', 'G-M', 'G-R', 'H-K', 'H-R', 'I-L', 'I-R', 'K-M', 'K-P', 'K-R', 'L-M', 'L-N', 'L-Q', 'L-R', 'M-R', 'N-R', 'P-R', 'Q-R', 'R-S', 'R-T', 'R-V', 'R-W', 'R-Y', 'A+S', 'C+T', 'neg', 'pol_pol', 'non_non', 'aro_aro', 'aro_neg', 'neg_neg']
SUBS_RAND = ['H', 'M', 'Y', 'C-D', 'C-M', 'C-N', 'D-M', 'D-Q', 'D-T', 'E-N', 'E-V', 'F-Q', 'F-W', 'H-T', 'H-Y', 'I-W', 'M-N', 'M-Q', 'M-V', 'S-Y', 'T-V', 'A+C', 'A+D', 'A+R', 'C+D', 'C+E', 'E+F', 'F+I', 'G+N', 'H+R', 'S+T', 'pol_pos', 'aro_pos', 'neg_pos']

FEATS_RECEP = [89.42, 90.2, 90.51, -1.99, -51, 90.24, 90.98, 90.51, 90.51, 'A+C', 'A+E', 'A+I', 'A+K', 'A+T', 'A-C', 'A-F', 'A-H', 'C+E', 'C+G', 'C+I', 'C+Y', 'C-K', 'C-T', 'D+F', 'D+G', 'D+H', 'D+I', 'D+N', 'D+P', 'D+S', 'E+G', 'E+S', 'E+T', 'E-N', 'E-S', 'F+R', 'F+T', 'F+Y', 'F-R', 'G+L', 'G+V', 'G-T', 'H-K', 'H-Q', 'H-T', 'I+K', 'K+W', 'M+Q', 'M-P', 'N-P', 'P-Q', 'P-R', 'Q-S', 'R-V', 'S-T', 'T+Y', 'T-V', 'W+Y', 'corr', 'pol_pos']
ADDS_RECEP = ['pos_pos', 'A', 'K', 'R', 'W', 'A-R', 'C-R', 'D-K', 'D-R', 'E-K', 'E-R', 'F-R', 'G-R', 'H-V', 'H-W', 'L-R', 'P-R', 'Q-R', 'R-S', 'R-T', 'R-V', 'W-Y', 'C+W', 'D+Y', 'aro_aro', 'neg_neg']
SUBS_RECEP = ['E', 'V', 'A-C', 'D-M', 'D-Y', 'E-N', 'G-Y', 'M-Q', 'M-S', 'P-T', 'Q-V', 'R-W', 'R-Y', 'A+C', 'C+Y', 'D+F', 'E+H', 'R+W', 'pol_pos']

CLASSIFIERS = {
    'rand': {
        'train_fasta': 'rand_train.fa',
        'feats': FEATS_RAND[9:],
        'adds': ADDS_RAND,
        'subs': SUBS_RAND,
    },
    'recep': {
        'train_fasta': 'recep_train.fa',
        'feats': FEATS_RECEP[9:],
        'adds': ADDS_RECEP,
        'subs': SUBS_RECEP,
    },
}
