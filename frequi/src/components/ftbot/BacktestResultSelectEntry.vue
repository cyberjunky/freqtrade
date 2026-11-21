<script setup lang="ts">
import type { BacktestResultInMemory } from '@/types';

withDefaults(
  defineProps<{
    backtestResult: BacktestResultInMemory;
    selectedBacktestResultKey?: string;
    canUseModify?: boolean;
  }>(),
  {
    selectedBacktestResultKey: '',
    canUseModify: false,
  },
);
</script>

<template>
  <div class="flex flex-col me-2 text-start">
    <div class="font-semibold font-mono text-[12.5px]">
      {{ backtestResult.metadata.strategyName }} - {{ backtestResult.strategy.timeframe }}
    </div>
    <div class="text-[12px] text-fg-2">
      {{ backtestResult.strategy.total_trades }} trades ·
      <span :class="profitClass(backtestResult.strategy.profit_total)" class="font-mono">{{
        formatSignedPercent(backtestResult.strategy.profit_total, 2)
      }}</span>
    </div>
    <div v-if="canUseModify" class="text-[12px] text-muted" style="white-space: pre-wrap">
      {{ backtestResult.metadata.notes }}
    </div>
  </div>
</template>
