<script setup lang="ts">
import type { BotUiState } from '@/composables/botInfo';

/** State = 9px dot + uppercase text label. */
const props = defineProps<{ state: BotUiState }>();

const LABELS: Record<BotUiState, string> = {
  running: 'Running',
  paused: 'Paused',
  stopped: 'Stopped',
  offline: 'Offline',
  reloading: 'Reloading',
  webserver: 'Webserver',
  unknown: 'Unknown',
};
const label = computed(() => LABELS[props.state]);
</script>

<template>
  <span class="ft-state" :class="`is-${state}`">
    <span class="ft-state-dot" aria-hidden="true"></span>{{ label }}
  </span>
</template>

<style scoped>
.ft-state {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  white-space: nowrap;
  color: var(--ft-text-2);
}
.ft-state-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--ft-idle);
  flex: 0 0 auto;
}
.is-running .ft-state-dot {
  background: var(--ft-success);
}
.is-running {
  color: var(--ft-success);
}
.is-paused .ft-state-dot,
.is-reloading .ft-state-dot {
  background: var(--ft-warning);
}
.is-paused,
.is-reloading {
  color: var(--ft-warning);
}
.is-stopped .ft-state-dot {
  background: var(--ft-danger);
}
.is-stopped {
  color: var(--ft-danger);
}
.is-offline .ft-state-dot {
  background: transparent;
  border: 2px solid var(--ft-idle);
}
.is-offline {
  color: var(--ft-muted);
}
.is-webserver .ft-state-dot {
  background: var(--ft-primary);
}
</style>
