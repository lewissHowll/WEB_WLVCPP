"""FASTA parsing utilities, refactored from the original WLVCPP.py script.

Logic is unchanged from the original — only reorganised into importable,
typed functions (no CLI side effects).
"""
from typing import List, Tuple


def from_fasta(fasta_path: str) -> Tuple[List[str], List[str]] | List[str]:
    """Read a FASTA file used for training (entries labelled 'cpp'/'non' in the header).

    Returns (cpps, ncpps) if headers contain those labels, otherwise a flat
    peptide list.
    """
    peptides, cpps, ncpps = [], [], []
    with open(fasta_path) as sf:
        for line in sf:
            if 'cpp' in line:
                line = sf.readline()
                cpps.append(line.strip('\n'))
            elif 'non' in line:
                line = sf.readline()
                ncpps.append(line.strip('\n'))
            elif '>' in line:
                line = sf.readline()
                peptides.append(line.strip('\n'))
    if peptides:
        return peptides
    return cpps, ncpps


def to_fasta(cpps: List[str], ncpps: List[str], fasta_name: str) -> None:
    with open(fasta_name, 'w') as tf:
        for k, pep in enumerate(cpps, start=1):
            tf.write(f'>cpp_{k}\n{pep}\n')
        for k, pep in enumerate(ncpps, start=1):
            tf.write(f'>non_{k}\n{pep}\n')


def check_entries(fasta_text_lines: List[str]) -> Tuple[List[str], List[str], List[List[str]]]:
    """Parse arbitrary user-submitted FASTA-ish text into (names, peptides, discarded).

    Tolerant of blank lines, lowercase, and non-alphabetic entries — matches
    the original script's permissive behaviour (see readme.md note 2).
    `fasta_text_lines` should be the file content already split into lines
    (no trailing newlines needed either way, both are stripped).
    """
    peps, names, nonalphabetic = [], [], []
    name, pep = '', ''
    for k, raw_line in enumerate(fasta_text_lines, start=1):
        name = pep + ''
        pep = raw_line.strip('\n').strip('\r')
        if '>' not in pep:
            if '>' in name:
                parts = name.strip('>').strip('\n').split()
                name = parts[0] if parts else f'line_{k}'
            else:
                name = f'line_{k}'

            if pep.isalpha():
                peps.append(pep)
                names.append(name)
            else:
                nonalphabetic.append([f'line_{k}', pep])
    return names, peps, nonalphabetic
