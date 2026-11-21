<script setup lang="ts">
import { useClipboard } from '@vueuse/core';

withDefaults(
  defineProps<{
    content: string | string[];
    isValid?: boolean;
  }>(),
  {
    isValid: true,
  },
);

const { copy, isSupported, copied } = useClipboard();
</script>

<template>
  <div class="copy-container">
    <button
      v-if="isSupported && isValid"
      type="button"
      class="ft-copy-btn"
      :title="copied ? 'Copied' : 'Copy to clipboard'"
      @click="copy(typeof content === 'string' ? content : JSON.stringify(content))"
    >
      <i-mdi-check-circle v-if="copied" aria-hidden="true" />
      <i-mdi-content-copy v-else aria-hidden="true" />
      <span>{{ copied ? 'Copied' : 'Copy' }}</span>
    </button>
    <pre class="ft-copy-pre ft-mono"><code>{{ content }}</code></pre>
  </div>
</template>

<style scoped>
.copy-container {
  position: relative;
}
.ft-copy-btn {
  position: absolute;
  right: 8px;
  top: 8px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: var(--ft-h-control-sm);
  padding: 0 8px;
  border: 1px solid var(--ft-border);
  border-radius: var(--ft-radius-control);
  background: var(--ft-panel);
  color: var(--ft-text-2);
  font-size: 11.5px;
  cursor: pointer;
}
.ft-copy-btn:hover {
  color: var(--ft-text);
}
.ft-copy-pre {
  text-align: start;
  border: 1px solid var(--ft-border);
  border-radius: var(--ft-radius-control);
  background: var(--ft-page);
  padding: 10px 12px;
  margin: 0;
  overflow: auto;
  font-size: 12px;
  max-height: 60vh;
}
</style>
