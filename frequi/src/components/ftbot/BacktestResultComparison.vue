<script setup lang="ts">
import type { BacktestResultInMemory } from '@/types';

const props = withDefaults(
  defineProps<{
    backtestResults: Record<string, BacktestResultInMemory>;
  }>(),
  {},
);

const backtestResultStats = computed(() => {
  const values = {};
  Object.entries(props.backtestResults).forEach(([key, result]) => {
    const tmp = generateBacktestMetricRows(result.strategy);
    values[key] = tmp;
  });
  console.log(values);
  // return '';
  return formatObjectForTable(values, 'metric');
});

const backtestResultFields = computed(() => {
  const res = [{ key: 'metric', label: 'Metric' }];
  Object.entries(props.backtestResults).forEach(([key, value]) => {
    res.push({ key, label: value.metadata.strategyName });
  });
  return res;
});
</script>

<template>
  <FtPanel title="Backtest result comparison" flush>
    <DataTable :value="backtestResultStats" size="small" scrollable>
      <Column
        v-for="col in backtestResultFields"
        :key="col.key"
        :field="col.key"
        :label="col.label"
      >
        <template #header>
          <BacktestResultSelectEntry
            v-if="col.key && backtestResults[col.key]"
            :backtest-result="backtestResults[col.key]!"
          />
          <span v-else>{{ col.label }}</span>
        </template>
      </Column>
    </DataTable>
  </FtPanel>
</template>
