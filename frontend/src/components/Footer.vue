<template>
  <footer class="site-footer">
    <div class="footer-inner">
      <div class="footer-note">
        <p>WLVCPP predictor · scores are the mean of two SVM classifiers trained on curated CPP/non-CPP peptide sets.</p>
      </div>
      <div class="collaborators">
        <span class="collaborators-label">Collaborators</span>
        <ul class="collaborators-list">
          <li v-for="c in collaborators" :key="c.name">
            {{ c.name }}<span v-if="c.role" class="role"> — {{ c.role }}</span>
          </li>
        </ul>
      </div>
    </div>
  </footer>
</template>

<script setup>
const collaborators = [
  { name: 'Bahaa Ismail', role: 'Original algorithm' },
  { name: 'Lewis Howl', role: 'Web application' },
  { name: 'Sarah Jones' },
  { name: 'John Howl' },
]
</script>

<style scoped>
.site-footer {
  border-top: 1px solid var(--hairline);
  margin-top: 40px;
}

.footer-inner {
  max-width: 1080px;
  margin: 0 auto;
  padding: 24px 24px 40px;
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 20px;
  font-size: 0.8rem;
  color: var(--ink-soft);
}

.footer-note {
  max-width: 480px;
}
.footer-note p {
  margin: 0;
}

.collaborators-label {
  display: block;
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ink-soft);
  margin-bottom: 6px;
}

.collaborators-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.collaborators-list li {
  color: var(--ink);
}
.role {
  color: var(--ink-soft);
}

@media (max-width: 600px) {
  .footer-inner {
    flex-direction: column;
  }
}
</style>
