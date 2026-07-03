// Mirrors wlvcpp/features.py AAGROUPS — the model's own physicochemical
// grouping of residues. Used for the live colour-coded sequence strip.
export const AA_GROUPS = {
  pol: { label: 'Polar', residues: ['S', 'T', 'C', 'P', 'N', 'Q'], color: 'var(--grp-pol)' },
  non: { label: 'Nonpolar', residues: ['G', 'A', 'V', 'L', 'I', 'M'], color: 'var(--grp-non)' },
  aro: { label: 'Aromatic', residues: ['F', 'Y', 'W'], color: 'var(--grp-aro)' },
  pos: { label: 'Positive', residues: ['K', 'R', 'H'], color: 'var(--grp-pos)' },
  neg: { label: 'Negative', residues: ['D', 'E'], color: 'var(--grp-neg)' },
}

const AA_TO_GROUP = {}
for (const [key, g] of Object.entries(AA_GROUPS)) {
  for (const r of g.residues) AA_TO_GROUP[r] = key
}

export function groupOf(residue) {
  return AA_TO_GROUP[residue?.toUpperCase()] || null
}

export function colorOf(residue) {
  const g = groupOf(residue)
  return g ? AA_GROUPS[g].color : 'var(--hairline)'
}
