<template>
  <div class="page">
    <header class="header">
      <div class="header-inner">
        <h1 class="wordmark">WLVCPP</h1>
        <p class="tagline">Cell-penetrating peptide predictor</p>
      </div>
    </header>

    <main class="layout">
      <!-- Input panel -->
      <section class="panel input-panel">
        <div class="panel-head">
          <h2>Sequences</h2>
          <label class="upload-btn">
            Upload FASTA
            <input type="file" accept=".fa,.fasta,.txt" @change="onFileUpload" hidden />
          </label>
        </div>

        <textarea
          v-model="fastaText"
          class="fasta-input"
          spellcheck="false"
          placeholder=">my_peptide&#10;KWKLFKKIEKVGQNIRDGIIKAGPAVAVVGQATQIAK&#10;>another_one&#10;GRKKRRQRRRPPQ"
        ></textarea>

        <div v-if="parsedEntries.length" class="live-preview">
          <div v-for="entry in parsedEntries.slice(0, 8)" :key="entry.name" class="preview-row">
            <span class="preview-name">{{ entry.name }}</span>
            <SequenceStrip :sequence="entry.sequence" />
          </div>
          <p v-if="parsedEntries.length > 8" class="preview-more">
            +{{ parsedEntries.length - 8 }} more entr{{ parsedEntries.length - 8 === 1 ? 'y' : 'ies' }}
          </p>
        </div>

        <div class="actions">
          <button class="predict-btn" :disabled="!fastaText.trim() || loading" @click="runPrediction">
            {{ loading ? 'Predicting…' : 'Predict' }}
          </button>
          <span v-if="entryCount" class="entry-count">{{ entryCount }} entr{{ entryCount === 1 ? 'y' : 'ies' }} detected</span>
        </div>

        <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>
      </section>

      <!-- Legend -->
      <aside class="panel legend-panel">
        <h2>Residue groups</h2>
        <p class="legend-note">The model groups amino acids by physicochemical property — this is what colours the sequences.</p>
        <ul class="legend-list">
          <li v-for="(g, key) in AA_GROUPS" :key="key">
            <span class="swatch" :style="{ background: g.color }"></span>
            <span class="legend-label">{{ g.label }}</span>
            <span class="legend-residues">{{ g.residues.join(' ') }}</span>
          </li>
        </ul>
      </aside>

      <!-- Results -->
      <section v-if="results" class="panel results-panel">
        <h2>Results</h2>

        <div v-if="results.predictions.length" class="results-table">
          <div class="results-row results-head">
            <span>Name</span>
            <span>Sequence</span>
            <span>Class</span>
            <span>Probability</span>
          </div>
          <div v-for="r in results.predictions" :key="r.name + r.peptide" class="results-row">
            <span class="cell-name">{{ r.name }}</span>
            <span class="cell-seq"><SequenceStrip :sequence="r.peptide" /></span>
            <span class="cell-class">
              <span class="badge" :class="r.predicted_class === 'CPP' ? 'badge-cpp' : 'badge-noncpp'">
                {{ r.predicted_class }}
              </span>
            </span>
            <span class="cell-prob">
              <span class="prob-track">
                <span
                  class="prob-fill"
                  :style="{ width: (r.probability * 100) + '%', background: r.predicted_class === 'CPP' ? 'var(--cpp)' : 'var(--noncpp)' }"
                ></span>
              </span>
              <span class="prob-value">{{ (r.probability * 100).toFixed(1) }}%</span>
            </span>
          </div>
        </div>

        <div v-if="results.discarded.length" class="discarded">
          <h3>Discarded entries</h3>
          <p class="discarded-note">Blank or non-alphabetic content — not scored.</p>
          <ul>
            <li v-for="d in results.discarded" :key="d.line">
              <span class="discarded-line">{{ d.line }}</span>
              <span class="discarded-content">{{ d.content || '(blank)' }}</span>
            </li>
          </ul>
        </div>
      </section>
    </main>

    <footer class="footer">
      <p>WLVCPP predictor · scores are the mean of two SVM classifiers trained on curated CPP/non-CPP peptide sets.</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import SequenceStrip from './components/SequenceStrip.vue'
import { AA_GROUPS } from './aminoAcids.js'

const fastaText = ref('')
const loading = ref(false)
const errorMessage = ref('')
const results = ref(null)

// Lightweight client-side FASTA parse, just for the live preview strip.
// The backend does the authoritative parsing (handles more edge cases).
const parsedEntries = computed(() => {
  const lines = fastaText.value.split(/\r?\n/)
  const entries = []
  let current = null
  for (const line of lines) {
    const trimmed = line.trim()
    if (!trimmed) continue
    if (trimmed.startsWith('>')) {
      if (current) entries.push(current)
      const nameMatch = trimmed.slice(1).trim().split(/\s+/)[0]
      current = { name: nameMatch || `entry_${entries.length + 1}`, sequence: '' }
    } else if (current && /^[A-Za-z]+$/.test(trimmed)) {
      current.sequence += trimmed.toUpperCase()
    }
  }
  if (current) entries.push(current)
  return entries.filter(e => e.sequence.length > 0)
})

const entryCount = computed(() => parsedEntries.value.length)

function onFileUpload(e) {
  const file = e.target.files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (ev) => {
    fastaText.value = ev.target.result
  }
  reader.readAsText(file)
}

async function runPrediction() {
  errorMessage.value = ''
  results.value = null
  loading.value = true
  try {
    const res = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fasta: fastaText.value }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail || `Request failed (${res.status})`)
    }
    results.value = await res.json()
  } catch (err) {
    errorMessage.value = err.message || 'Something went wrong. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page {
  max-width: 1080px;
  margin: 0 auto;
  padding: 0 24px 64px;
}

.header {
  padding: 48px 0 32px;
  border-bottom: 1px solid var(--hairline);
  margin-bottom: 32px;
}
.wordmark {
  font-family: var(--font-display);
  font-size: 2.25rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  margin: 0;
}
.tagline {
  margin: 4px 0 0;
  color: var(--ink-soft);
  font-size: 1rem;
}

.layout {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
}
@media (max-width: 760px) {
  .layout { grid-template-columns: 1fr; }
}

.panel {
  background: var(--paper-raised);
  border: 1px solid var(--hairline);
  border-radius: 8px;
  padding: 24px;
}
.panel h2 {
  font-family: var(--font-display);
  font-size: 1.05rem;
  font-weight: 600;
  margin: 0 0 16px;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.panel-head h2 { margin: 0; }

.upload-btn {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--grp-pos);
  border: 1px solid var(--hairline);
  border-radius: 6px;
  padding: 6px 12px;
  cursor: pointer;
  transition: border-color 0.15s;
}
.upload-btn:hover { border-color: var(--grp-pos); }

.fasta-input {
  width: 100%;
  min-height: 160px;
  font-family: var(--font-mono);
  font-size: 0.9rem;
  padding: 14px;
  border: 1px solid var(--hairline);
  border-radius: 6px;
  background: var(--paper);
  color: var(--ink);
  resize: vertical;
  line-height: 1.5;
}

.live-preview {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed var(--hairline);
}
.preview-row {
  display: flex;
  gap: 12px;
  align-items: baseline;
  padding: 4px 0;
  font-size: 0.85rem;
}
.preview-name {
  font-weight: 500;
  color: var(--ink-soft);
  min-width: 110px;
  flex-shrink: 0;
}
.preview-more {
  color: var(--ink-soft);
  font-size: 0.8rem;
  margin: 6px 0 0;
}

.actions {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 18px;
}
.predict-btn {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 0.95rem;
  background: var(--ink);
  color: var(--paper);
  border: none;
  border-radius: 6px;
  padding: 11px 22px;
  cursor: pointer;
  transition: opacity 0.15s;
}
.predict-btn:hover:not(:disabled) { opacity: 0.85; }
.predict-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.entry-count {
  font-size: 0.85rem;
  color: var(--ink-soft);
}

.error-msg {
  margin-top: 12px;
  color: var(--grp-neg);
  font-size: 0.9rem;
}

.legend-note {
  font-size: 0.85rem;
  color: var(--ink-soft);
  margin: -8px 0 16px;
}
.legend-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.legend-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 0;
  border-bottom: 1px solid var(--hairline);
  font-size: 0.85rem;
}
.legend-list li:last-child { border-bottom: none; }
.swatch {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex-shrink: 0;
}
.legend-label { font-weight: 500; min-width: 70px; }
.legend-residues {
  font-family: var(--font-mono);
  color: var(--ink-soft);
  font-size: 0.8rem;
}

.results-panel {
  grid-column: 1 / -1;
}
.results-table {
  display: flex;
  flex-direction: column;
}
.results-row {
  display: grid;
  grid-template-columns: 140px 1fr 90px 180px;
  gap: 16px;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--hairline);
  font-size: 0.9rem;
}
.results-head {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--ink-soft);
  border-bottom: 1px solid var(--ink);
}
.cell-name { font-weight: 500; }
.cell-seq { overflow-wrap: anywhere; }

.badge {
  font-family: var(--font-display);
  font-size: 0.75rem;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 100px;
  color: #fff;
}
.badge-cpp { background: var(--cpp); }
.badge-noncpp { background: var(--noncpp); }

.cell-prob {
  display: flex;
  align-items: center;
  gap: 8px;
}
.prob-track {
  flex: 1;
  height: 6px;
  border-radius: 4px;
  background: var(--hairline);
  overflow: hidden;
}
.prob-fill {
  display: block;
  height: 100%;
}
.prob-value {
  font-family: var(--font-mono);
  font-size: 0.78rem;
  color: var(--ink-soft);
  min-width: 42px;
  text-align: right;
}

.discarded {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid var(--hairline);
}
.discarded h3 {
  font-family: var(--font-display);
  font-size: 0.9rem;
  margin: 0 0 4px;
}
.discarded-note {
  font-size: 0.8rem;
  color: var(--ink-soft);
  margin: 0 0 10px;
}
.discarded ul { list-style: none; padding: 0; margin: 0; }
.discarded li {
  display: flex;
  gap: 12px;
  font-size: 0.82rem;
  padding: 3px 0;
  color: var(--ink-soft);
}
.discarded-line { font-family: var(--font-mono); min-width: 70px; }

.footer {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid var(--hairline);
  font-size: 0.8rem;
  color: var(--ink-soft);
}
</style>
