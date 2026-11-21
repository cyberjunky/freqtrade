<script setup lang="ts">
import type { StrategyBacktestResult } from '@/types';

const props = defineProps<{
  backtestResult: StrategyBacktestResult;
}>();

const backtestResultStats = computed(() => {
  const tmp = generateBacktestMetricRows(props.backtestResult);
  return formatObjectForTable({ value: tmp }, 'metric');
});

const backtestResultSettings = computed(() => {
  // Transpose Result into readable format
  const tmp = generateBacktestSettingRows(props.backtestResult);

  return formatObjectForTable({ value: tmp }, 'setting');
});
</script>

<template>
  <div class="px-0 w-full">
    <h2 class="ft-title mb-3">
      Backtest result for <span class="ft-mono">{{ backtestResult.strategy_name }}</span>
    </h2>

    <div class="ft-stack">
      <div class="ft-grid-2">
        <div class="min-w-0">
          <FtPanel title="Strategy settings" flush>
            <DataTable size="small" :value="backtestResultSettings">
              <Column field="setting" header="Setting"></Column>
              <Column field="value" header="Value" class="ft-num"></Column>
            </DataTable>
          </FtPanel>
        </div>
        <div class="min-w-0">
          <FtPanel title="Metrics" flush>
            <DataTable size="small" borderless :value="backtestResultStats">
              <Column field="metric" header="Metric" />
              <Column field="value" header="Value" class="ft-num" />
            </DataTable>
          </FtPanel>
        </div>
      </div>
      <BacktestResultTablePer
        title="Results per Enter tag"
        :results="backtestResult.results_per_enter_tag"
        :stake-currency="backtestResult.stake_currency"
        key-header="Enter Tag"
        :stake-currency-decimals="backtestResult.stake_currency_decimals"
      />

      <BacktestResultTablePer
        title="Results per Exit reason"
        :results="backtestResult.exit_reason_summary ?? []"
        :stake-currency="backtestResult.stake_currency"
        key-header="Exit Reason"
        :stake-currency-decimals="backtestResult.stake_currency_decimals"
      />

      <BacktestResultTablePer
        v-if="backtestResult.mix_tag_stats"
        title="Results Mixed Tag"
        :results="backtestResult.mix_tag_stats ?? []"
        :stake-currency="backtestResult.stake_currency"
        :key-headers="['Enter Tag', 'Exit Tag']"
        :stake-currency-decimals="backtestResult.stake_currency_decimals"
      />

      <BacktestResultTablePer
        title="Results per pair"
        :results="backtestResult.results_per_pair"
        :stake-currency="backtestResult.stake_currency"
        key-header="Pair"
        :stake-currency-decimals="backtestResult.stake_currency_decimals"
      />
      <FtPanel v-if="backtestResult.periodic_breakdown" title="Periodic breakdown" flush>
        <BacktestResultPeriodBreakdown :periodic-breakdown="backtestResult.periodic_breakdown">
        </BacktestResultPeriodBreakdown>
      </FtPanel>

      <FtPanel title="Single trades" flush>
        <TradeList
          :trades="backtestResult.trades"
          :show-filter="true"
          :stake-currency="backtestResult.stake_currency"
        />
      </FtPanel>
    </div>
  </div>
</template>
