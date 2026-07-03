<template>
  <nav class="navbar">
    <div class="navbar-inner">
      <router-link to="/" class="brand">
        <span class="brand-mark">WLVCPP</span>
      </router-link>
      <div class="nav-links">
        <router-link to="/" class="nav-link" exact-active-class="nav-link-active">Home</router-link>
        <router-link to="/contact" class="nav-link" exact-active-class="nav-link-active">Contact</router-link>
      </div>
    </div>
  </nav>
</template>

<script setup>
</script>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--paper-raised);
  border-bottom: 1px solid var(--hairline);
}

.navbar-inner {
  max-width: 1080px;
  margin: 0 auto;
  padding: 0 24px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand {
  text-decoration: none;
}
.brand-mark {
  font-family: var(--font-display);
  font-weight: 700;
  font-size: 1.15rem;
  letter-spacing: -0.01em;
  color: var(--ink);
}

.nav-links {
  display: flex;
  gap: 4px;
}

.nav-link {
  font-family: var(--font-body);
  font-weight: 500;
  font-size: 0.9rem;
  color: var(--ink-soft);
  text-decoration: none;
  padding: 8px 14px;
  border-radius: 6px;
  transition: background 0.15s, color 0.15s;
}
.nav-link:hover {
  background: var(--paper);
  color: var(--ink);
}
.nav-link-active {
  color: var(--ink);
  background: var(--paper);
}
</style>
