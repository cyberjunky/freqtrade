<script setup lang="ts">
/** KPI tile strip: one bordered group, the divider colour shows through the 1px gaps. */
</script>

<template>
  <div class="ft-tiles" role="list">
    <slot />
  </div>
</template>

<style scoped>
.ft-tiles {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 1px;
  background: var(--ft-border);
  border: 1px solid var(--ft-border);
  border-radius: var(--ft-radius-panel);
  overflow: hidden;
}
@media (max-width: 700px) {
  .ft-tiles {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }
}
</style>
