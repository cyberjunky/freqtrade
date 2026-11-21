<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    label: string;
    /** Preformatted value */
    value?: string | number;
    /** Secondary line below the value */
    sub?: string;
    /** When set the value is treated as a P&L: coloured pos / neg (the sign is part of `value`) */
    profit?: number | null;
    hint?: string;
  }>(),
  { value: undefined, sub: '', profit: undefined, hint: '' },
);

const valueClass = computed(() => (props.profit === undefined ? '' : profitClass(props.profit)));
</script>

<template>
  <div class="ft-tile" role="listitem" :title="hint || undefined">
    <div class="ft-tile-label">{{ label }}</div>
    <div class="ft-tile-value ft-mono" :class="valueClass">
      <slot>{{ value ?? '-' }}</slot>
    </div>
    <div v-if="sub || $slots.sub" class="ft-tile-sub ft-mono">
      <slot name="sub">{{ sub }}</slot>
    </div>
  </div>
</template>

<style scoped>
.ft-tile {
  background: var(--ft-panel);
  padding: 12px 16px 12px;
  min-width: 0;
}
.ft-tile-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--ft-text-2);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ft-tile-value {
  font-size: 24px;
  font-weight: 600;
  line-height: 1.25;
  margin-top: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ft-tile-sub {
  font-size: 11.5px;
  color: var(--ft-muted);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
@media (max-width: 700px) {
  .ft-tile {
    padding: 10px 12px;
  }
  .ft-tile-value {
    font-size: 20px;
  }
}
</style>
