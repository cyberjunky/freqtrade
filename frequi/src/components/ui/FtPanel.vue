<script setup lang="ts">
/** Panel: background + 1px border, radius 6px, no shadow. */
withDefaults(
  defineProps<{
    title?: string;
    /** Remove the body padding (tables, charts that go edge to edge) */
    flush?: boolean;
    /** Body height (charts) */
    bodyHeight?: string;
  }>(),
  { title: '', flush: false, bodyHeight: undefined },
);
</script>

<template>
  <section class="ft-panel">
    <header v-if="title || $slots.title || $slots.actions" class="ft-panel-head">
      <h2 class="ft-title ft-panel-title">
        <slot name="title">{{ title }}</slot>
      </h2>
      <div v-if="$slots.actions" class="ft-panel-actions"><slot name="actions" /></div>
    </header>
    <div
      class="ft-panel-body"
      :class="{ 'is-flush': flush }"
      :style="bodyHeight ? { height: bodyHeight } : undefined"
    >
      <slot />
    </div>
  </section>
</template>

<style scoped>
.ft-panel {
  background: var(--ft-panel);
  border: 1px solid var(--ft-border);
  border-radius: var(--ft-radius-panel);
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.ft-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px 12px;
  min-height: 42px;
  padding: 6px 12px 6px 18px;
  border-bottom: 1px solid var(--ft-border);
}
.ft-panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
}
.ft-panel-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  min-width: 0;
}
.ft-panel-body {
  padding: var(--ft-pad-panel);
  min-width: 0;
  flex: 1 1 auto;
}
.ft-panel-body.is-flush {
  padding: 0;
}
@media (max-width: 700px) {
  .ft-panel-head {
    padding-left: 12px;
  }
  .ft-panel-body:not(.is-flush) {
    padding: 12px;
  }
}
</style>
