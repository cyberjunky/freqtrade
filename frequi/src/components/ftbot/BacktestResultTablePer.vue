<script setup lang="ts">
import type { ExitReasonResults, PairResult } from '@/types';

type ResultsType = PairResult | ExitReasonResults;
type ResultsTypeWithKey = ResultsType & { key?: string | string[] };
const props = withDefaults(
  defineProps<{
    title: string;
    results: ResultsType[];
    stakeCurrency: string;
    stakeCurrencyDecimals: number;
    keyHeader?: string;
    keyHeaders?: string[];
  }>(),
  {
    keyHeader: '',
    keyHeaders: () => [],
  },
);

const tableItems = computed<ResultsTypeWithKey[]>(() =>
  props.results.map((v) => {
    if (props.keyHeaders.length > 0) {
      return {
        ...v,
        key:
          typeof v['key'] === 'string' ? Array(props.keyHeaders.length).fill(v['key']) : v['key'],
      };
    }
    return v;
  }),
);

const perTagReason = computed(() => {
  const firstFields: {
    key: string;
    label: string;
    formatter: (value: string, item: ResultsTypeWithKey) => string;
  }[] = [];
  if (props.keyHeaders.length > 0) {
    // Keys could be an array
    for (const [i, header] of props.keyHeaders.entries()) {
      firstFields.push({
        key: `key[${i}]`,
        label: header,
        formatter: (value, item) =>
          Array.isArray(value) ? value[i] : value || item['exit_reason'] || 'OTHER',
      });
    }
  } else {
    firstFields.push({
      key: 'key',
      label: props.keyHeader,
      formatter: (value, item) => (value || item['exit_reason'] || 'OTHER') as string,
    });
  }
  return firstFields;
});

const settingsStore = useSettingsStore();

const metrics = computed(() =>
  availableBacktestMetrics.value.filter(
    (metric) =>
      metric.field !== 'key' && settingsStore.backtestAdditionalMetrics.includes(metric.field),
  ),
);
</script>
<template>
  <FtPanel :title="title" flush>
    <template #actions>
      <span class="ft-hint">Shown metrics</span>
      <MultiSelect
        id="backtestMetrics"
        v-model="settingsStore.backtestAdditionalMetrics"
        :options="availableBacktestMetrics"
        option-label="header"
        option-value="field"
        size="small"
        aria-label="Shown metrics"
        :max-selected-labels="2"
      />
    </template>
    <DataTable size="small" scrollable :value="tableItems">
      <Column v-for="col in perTagReason" :key="col.key" :field="col.key" :header="col.label">
        <template #body="{ data }">
          {{ col.formatter(data['key'], data) }}
        </template>
      </Column>
      <Column class="ft-num" field="trades" header="Trades"></Column>
      <Column class="ft-num" field="profit_mean" header="Avg Profit %">
        <template #body="{ data, field }">
          {{ formatPercent(data[field as string], 2) }}
        </template>
      </Column>
      <Column class="ft-num" field="profit_total_abs" :header="`Tot Profit ${props.stakeCurrency}`">
        <template #body="{ data, field }">
          {{ formatPrice(data[field as string], props.stakeCurrencyDecimals) }}
        </template>
      </Column>
      <Column class="ft-num" field="profit_total" header="Tot Profit %">
        <template #body="{ data, field }">
          {{ formatPercent(data[field as string], 2) }}
        </template>
      </Column>
      <Column class="ft-num" field="wins" header="Wins"></Column>
      <Column class="ft-num" field="draws" header="Draws"></Column>
      <Column class="ft-num" field="losses" header="Losses"></Column>

      <Column
        v-for="col in metrics"
        :key="col.field"
        class="ft-num"
        :field="col.field"
        :header="col.header"
      >
        <template #body="{ data, field }">
          {{
            col.is_ratio
              ? formatPercent(data[field as string], 2)
              : formatPrice(data[field as string], 2)
          }}
        </template>
      </Column>
    </DataTable>
  </FtPanel>
</template>
