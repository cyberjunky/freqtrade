<script setup lang="ts">
/**
 * Profit value: "+1.23% (+0.456)". Always carries a sign and is coloured pos / neg -
 * the colour is never the only signal.
 */
const props = defineProps<{
  profitRatio?: number | null;
  profitAbs?: number;
  stakeCurrency: string;
  profitDesc?: string;
}>();
const isProfitable = computed<boolean | null>(() => {
  if (!isDefined(props.profitRatio) && !isDefined(props.profitAbs)) {
    return null;
  }
  return (
    (isDefined(props.profitRatio) && props.profitRatio > 0) ||
    (props.profitRatio === undefined && props.profitAbs !== undefined && props.profitAbs > 0)
  );
});

const isZero = computed(
  () => isProfitable.value === false && !props.profitRatio && !props.profitAbs,
);

const profitString = computed((): string => {
  if (props.profitRatio !== undefined && props.profitAbs !== undefined) {
    return `(${formatSigned(props.profitAbs, 3)})`;
  } else if (props.profitAbs !== undefined) {
    if (props.stakeCurrency !== undefined) {
      return `${signOf(props.profitAbs)}${formatPriceCurrency(props.profitAbs, props.stakeCurrency, 3)}`;
    } else {
      return formatSigned(props.profitAbs, 3);
    }
  }
  return '';
});
</script>

<template>
  <div
    class="ft-profit-pill ft-mono"
    :class="{
      'profit-pill-profit': isProfitable === true,
      'profit-pill': isProfitable === false,
      'is-zero': isZero,
      'border-surface-500': isProfitable === null,
    }"
    :title="profitDesc"
  >
    {{ isDefined(profitRatio) ? formatSignedPercent(profitRatio, 2) : '' }}
    <span
      v-if="profitString"
      :class="{ 'ft-profit-abs': isDefined(profitRatio) }"
      :title="stakeCurrency"
      >{{ profitString }}</span
    >
    <template v-if="isProfitable === null">-</template>
  </div>
</template>

<style scoped lang="css">
.ft-profit-pill {
  display: inline-flex;
  align-items: baseline;
  justify-content: flex-end;
  gap: 6px;
  white-space: nowrap;
  border: 0;
  color: var(--ft-muted);
}
.profit-pill {
  color: var(--ft-neg);
}
.profit-pill-profit {
  color: var(--ft-pos);
}
.profit-pill.is-zero {
  color: var(--ft-muted);
}
.ft-profit-abs {
  font-size: 0.92em;
  opacity: 0.85;
}
</style>
