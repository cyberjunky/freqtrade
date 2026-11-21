<script setup lang="ts">
withDefaults(defineProps<{ title?: string; text?: string }>(), { title: '', text: '' });
</script>

<template>
  <div class="ft-empty">
    <div v-if="$slots.icon" class="ft-empty-icon"><slot name="icon" /></div>
    <div v-if="title" class="ft-empty-title">{{ title }}</div>
    <div v-if="text || $slots.default" class="ft-empty-text">
      <slot>{{ text }}</slot>
    </div>
    <div v-if="$slots.actions" class="ft-empty-actions"><slot name="actions" /></div>
  </div>
</template>

<style scoped>
.ft-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 6px;
  padding: 28px 16px;
  color: var(--ft-muted);
  min-height: 120px;
  height: 100%;
}
.ft-empty-icon {
  font-size: 26px;
  color: var(--ft-idle);
}
.ft-empty-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--ft-text-2);
}
.ft-empty-text {
  font-size: 12.5px;
  max-width: 48ch;
}
.ft-empty-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
}
</style>
