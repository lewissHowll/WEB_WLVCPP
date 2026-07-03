<template>
  <span class="strip" :aria-label="sequence">
    <span
      v-for="(res, i) in chars"
      :key="i"
      class="residue"
      :style="{ color: colorOf(res) }"
      :title="groupOf(res) ? AA_GROUPS[groupOf(res)].label : 'Unrecognised residue'"
    >{{ res }}</span>
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { colorOf, groupOf, AA_GROUPS } from '../aminoAcids.js'

const props = defineProps({
  sequence: { type: String, default: '' },
})

const chars = computed(() => props.sequence.split(''))
</script>

<style scoped>
.strip {
  font-family: var(--font-mono);
  font-size: 0.95em;
  letter-spacing: 0.02em;
  word-break: break-all;
}
.residue {
  font-weight: 600;
}
</style>
