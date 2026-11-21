<script setup lang="ts">
/** Profit / loss value: always signed, coloured, monospace. */
const props = withDefaults(
  defineProps<{
    abs?: number | null;
    ratio?: number | null;
    currency?: string;
    decimals?: number;
    /** Stack the ratio below the absolute value */
    stacked?: boolean;
  }>(),
  { abs: undefined, ratio: undefined, currency: '', decimals: 3, stacked: false },
);

const basis = computed(() => (isNotUndefined(props.abs) ? props.abs : props.ratio));
const hasAbs = computed(() => isNotUndefined(props.abs));
const hasRatio = computed(() => isNotUndefined(props.ratio) && !Number.isNaN(props.ratio));
</script>

<template>
  <span class="ft-profit ft-mono" :class="[profitClass(basis), { 'is-stacked': stacked }]">
    <template v-if="!hasAbs && !hasRatio">-</template>
    <span v-if="hasAbs"
      >{{ formatSigned(abs, decimals)
      }}<span v-if="currency" class="ft-profit-cur"> {{ currency }}</span></span
    >
    <span v-if="hasRatio" :class="{ 'ft-profit-ratio': hasAbs }">{{
      hasAbs ? `(${formatSignedPercent(ratio)})` : formatSignedPercent(ratio)
    }}</span>
  </span>
</template>

<style scoped>
.ft-profit {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  white-space: nowrap;
}
.ft-profit.is-stacked {
  flex-direction: column;
  align-items: flex-end;
  gap: 0;
}
.ft-profit-cur {
  font-size: 0.85em;
  opacity: 0.8;
}
.ft-profit-ratio {
  font-size: 0.92em;
  opacity: 0.85;
}
</style>
