<template>
  <div class="page">
    <div class="page-intro">
      <h1 class="page-title">Contact</h1>
    </div>

    <div class="panel form-panel">
      <p class="intro-text">
        Questions, bug reports, or feedback about a prediction — send a message and it'll land directly in the site owner's inbox.
      </p>

      <form v-if="!sent" @submit.prevent="submit" class="contact-form">
        <div class="field">
          <label for="name">Name</label>
          <input id="name" v-model="form.name" type="text" required autocomplete="name" />
        </div>

        <div class="field">
          <label for="email">Email</label>
          <input id="email" v-model="form.email" type="email" required autocomplete="email" />
        </div>

        <div class="field">
          <label for="subject">Subject</label>
          <input id="subject" v-model="form.subject" type="text" required />
        </div>

        <div class="field">
          <label for="comment">Message</label>
          <textarea id="comment" v-model="form.comment" required rows="6" maxlength="5000"></textarea>
        </div>

        <div class="actions">
          <button type="submit" class="submit-btn" :disabled="sending">
            {{ sending ? 'Sending…' : 'Send message' }}
          </button>
        </div>

        <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>
      </form>

      <div v-else class="sent-confirmation">
        <p class="sent-title">Message sent.</p>
        <p class="sent-body">Thanks, {{ form.name }} — this has been sent through, you should hear back soon.</p>
        <button class="submit-btn secondary" @click="resetForm">Send another message</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'

const form = reactive({ name: '', email: '', subject: '', comment: '' })
const sending = ref(false)
const sent = ref(false)
const errorMessage = ref('')

async function submit() {
  errorMessage.value = ''
  sending.value = true
  try {
    const res = await fetch('/api/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...form }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      const detail = Array.isArray(body.detail)
        ? body.detail.map(d => d.msg).join(', ')
        : body.detail
      throw new Error(detail || `Request failed (${res.status})`)
    }
    sent.value = true
  } catch (err) {
    errorMessage.value = err.message || 'Something went wrong. Please try again.'
  } finally {
    sending.value = false
  }
}

function resetForm() {
  form.name = ''
  form.email = ''
  form.subject = ''
  form.comment = ''
  sent.value = false
}
</script>

<style scoped>
.page {
  max-width: 640px;
  margin: 0 auto;
  padding: 0 24px 64px;
}

.page-intro {
  padding: 32px 0 28px;
  border-bottom: 1px solid var(--hairline);
  margin-bottom: 32px;
}
.page-title {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: -0.01em;
  margin: 0;
  color: var(--ink-soft);
}

.panel {
  background: var(--paper-raised);
  border: 1px solid var(--hairline);
  border-radius: 8px;
  padding: 28px;
}

.intro-text {
  margin: 0 0 24px;
  color: var(--ink-soft);
  font-size: 0.92rem;
  line-height: 1.5;
}

.contact-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.field label {
  font-family: var(--font-display);
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--ink);
}
.field input,
.field textarea {
  font-family: var(--font-body);
  font-size: 0.92rem;
  padding: 10px 12px;
  border: 1px solid var(--hairline);
  border-radius: 6px;
  background: var(--paper);
  color: var(--ink);
  resize: vertical;
}

.actions {
  margin-top: 4px;
}
.submit-btn {
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
.submit-btn:hover:not(:disabled) { opacity: 0.85; }
.submit-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.submit-btn.secondary {
  background: transparent;
  color: var(--ink);
  border: 1px solid var(--hairline);
}

.error-msg {
  margin: 0;
  color: var(--grp-neg);
  font-size: 0.9rem;
}

.sent-confirmation {
  text-align: center;
  padding: 20px 0;
}
.sent-title {
  font-family: var(--font-display);
  font-weight: 600;
  font-size: 1.1rem;
  color: var(--cpp);
  margin: 0 0 8px;
}
.sent-body {
  color: var(--ink-soft);
  font-size: 0.92rem;
  margin: 0 0 20px;
}
</style>
