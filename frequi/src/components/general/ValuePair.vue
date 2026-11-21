<script setup lang="ts">
withDefaults(
  defineProps<{
    description: string;
    help?: string;
    classLabel?: string;
    classValue?: string;
  }>(),
  {
    help: '',
    classLabel: '',
    classValue: '',
  },
);
</script>

<template>
  <div class="ft-vp">
    <div class="ft-vp-label" :class="classLabel">
      <label>{{ description }}</label>
      <InfoBox v-if="help" :hint="help" />
    </div>
    <div class="ft-vp-value ft-mono" :class="classValue">
      <slot></slot>
    </div>
  </div>
</template>

<style scoped>
.ft-vp {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 5px 0;
  border-bottom: 1px solid var(--ft-border);
  min-width: 0;
}
.ft-vp-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--ft-text-2);
  flex: 0 0 auto;
}
.ft-vp-value {
  text-align: right;
  min-width: 0;
  overflow-wrap: anywhere;
}
</style>
