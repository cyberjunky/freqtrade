<script setup lang="ts">
defineProps<{ hint: string }>();
</script>

<template>
  <span class="ft-info" :title="hint" tabindex="0" role="img" :aria-label="hint">
    <i-mdi-information-outline aria-hidden="true" />
  </span>
</template>

<style scoped>
.ft-info {
  display: inline-flex;
  color: var(--ft-muted);
  cursor: help;
}
</style>
