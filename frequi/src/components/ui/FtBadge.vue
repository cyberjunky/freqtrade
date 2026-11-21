<script setup lang="ts">
/** Badge: radius 3px, 11px 600, padding 1px 6px. */
withDefaults(
  defineProps<{
    /** default = tag colours, ok = green tint, bad = danger bg, warn = amber tint, neutral = grey bordered */
    kind?: 'default' | 'ok' | 'bad' | 'warn' | 'neutral';
  }>(),
  { kind: 'default' },
);
</script>

<template>
  <span class="ft-badge" :class="`is-${kind}`"><slot /></span>
</template>

<style scoped>
.ft-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  border-radius: var(--ft-radius-badge);
  font-size: 11px;
  font-weight: 600;
  line-height: 1.45;
  padding: 1px 6px;
  white-space: nowrap;
  letter-spacing: 0.02em;
  border: 1px solid transparent;
  background: var(--ft-tag-bg);
  color: var(--ft-tag-text);
}
.ft-badge.is-ok {
  background: var(--ft-success-bg);
  color: var(--ft-success);
}
.ft-badge.is-bad {
  background: var(--ft-danger-bg);
  color: var(--ft-danger);
}
.ft-badge.is-warn {
  background: var(--ft-warning-bg);
  color: var(--ft-warning);
}
.ft-badge.is-neutral {
  background: transparent;
  border-color: var(--ft-border);
  color: var(--ft-text-2);
}
</style>
