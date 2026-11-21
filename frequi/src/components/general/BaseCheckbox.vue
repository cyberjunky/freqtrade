<script setup lang="ts">
withDefaults(defineProps<{ disabled?: boolean }>(), {
  disabled: false,
});
const id = useId();
const value = defineModel<boolean>();
</script>

<template>
  <div class="ft-check">
    <div class="ft-check-row">
      <Checkbox v-model="value" binary size="small" :input-id="`input-${id}`" :disabled="disabled">
        <template #icon="{ checked }">
          <i-mdi-check-bold v-if="checked" />
        </template>
      </Checkbox>
      <label :for="`input-${id}`" class="ft-check-label"><slot /></label>
    </div>
    <small v-if="$slots.hint" class="ft-hint ft-check-hint">
      <slot name="hint"></slot>
    </small>
  </div>
</template>

<style scoped>
.ft-check-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.ft-check-label {
  font-size: 12.5px;
  cursor: pointer;
}
.ft-check-label:empty {
  display: none;
}
.ft-check-hint {
  display: block;
  margin: 2px 0 0 24px;
}
</style>
