<script setup lang="ts">
const botStore = useBotStore();
enum PerformanceOptions {
  performance = 'performance',
  entryStats = 'entryStats',
  exitStats = 'exitStats',
  mixTagStats = 'mixTagStats',
}
const selectedOption = ref<PerformanceOptions>(PerformanceOptions.performance);

function formatTextLen(text: string, len: number) {
  if (text.length > len) {
    return text.substring(0, len) + '...';
  }
  return text;
}

const performanceTable = computed<
  {
    key: string;
    label: string;
    formatter?: (v: unknown) => string;
  }[]
>(() => {
  const textLength = 17;
  const initialCol = {
    [PerformanceOptions.performance]: { key: 'pair', label: 'Pair' },
    [PerformanceOptions.entryStats]: {
      key: 'enter_tag',
      label: 'Enter tag',
      formatter: (v: unknown) => formatTextLen(v as string, textLength),
    },
    [PerformanceOptions.exitStats]: {
      key: 'exit_reason',
      label: 'Exit Reason',
      formatter: (v: unknown) => formatTextLen(v as string, textLength),
    },
    [PerformanceOptions.mixTagStats]: {
      key: 'mix_tag',
      label: 'Mix Tag',
      formatter: (v: unknown) => formatTextLen(v as string, textLength),
    },
  };
  return [
    initialCol[selectedOption.value],
    { key: 'profit_pct', label: 'Profit %' },
    {
      key: 'profit_abs',
      label: `Profit ${botStore.activeBot.botState?.stake_currency}`,
      formatter: (v: unknown) => formatPrice(v as number, 5),
    },
    { key: 'count', label: 'Count' },
  ];
});

const performanceData = computed(() => {
  if (selectedOption.value === PerformanceOptions.performance) {
    return botStore.activeBot.performanceStats;
  }
  if (selectedOption.value === PerformanceOptions.entryStats) {
    return botStore.activeBot.entryStats;
  }
  if (selectedOption.value === PerformanceOptions.exitStats) {
    return botStore.activeBot.exitStats;
  }
  if (selectedOption.value === PerformanceOptions.mixTagStats) {
    return botStore.activeBot.mixTagStats;
  }
  return [];
});

const options = [
  { value: PerformanceOptions.performance, text: 'Pairs' },
  { value: PerformanceOptions.entryStats, text: 'Entry tags' },
  { value: PerformanceOptions.exitStats, text: 'Exit reasons' },
  { value: PerformanceOptions.mixTagStats, text: 'Mix tags' },
];

function refreshSummary() {
  if (selectedOption.value === PerformanceOptions.performance) {
    botStore.activeBot.getPerformance();
  }
  if (selectedOption.value === PerformanceOptions.entryStats) {
    botStore.activeBot.getEntryStats();
  }
  if (selectedOption.value === PerformanceOptions.exitStats) {
    botStore.activeBot.getExitStats();
  }
  if (selectedOption.value === PerformanceOptions.mixTagStats) {
    botStore.activeBot.getMixTagStats();
  }
}

onMounted(() => {
  refreshSummary();
});
</script>
<template>
  <div>
    <div class="ft-perf-bar">
      <SelectButton
        v-if="botStore.activeBot.botFeatures.hasAdvancedStats"
        v-model="selectedOption"
        :options="options"
        :allow-empty="false"
        aria-label="Group by"
        option-label="text"
        option-value="value"
        size="small"
        @change="refreshSummary"
      ></SelectButton>
      <Button
        class="ms-auto"
        severity="secondary"
        size="small"
        title="Refresh"
        aria-label="Refresh"
        @click="refreshSummary"
      >
        <template #icon><i-mdi-refresh /></template>
      </Button>
    </div>
    <DataTable
      size="small"
      :value="performanceData"
      scrollable
      scroll-height="420px"
      removable-sort
    >
      <template #empty>No data.</template>
      <Column
        v-for="(field, idx) in performanceTable"
        :key="field.key"
        :field="field.key"
        :header="field.label"
        sortable
        :class="idx === 0 ? 'ft-mono' : 'ft-num'"
      >
        <template #body="slotProps">
          <span
            v-if="field.key === 'profit_pct' || field.key === 'profit_abs'"
            :class="profitClass(slotProps.data[field.key])"
            >{{ signOf(slotProps.data[field.key])
            }}{{
              field.formatter
                ? field.formatter(slotProps.data[field.key])
                : slotProps.data[field.key]
            }}{{ field.key === 'profit_pct' ? '%' : '' }}</span
          >
          <template v-else>{{
            field.formatter ? field.formatter(slotProps.data[field.key]) : slotProps.data[field.key]
          }}</template>
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<style scoped>
.ft-perf-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--ft-border);
}
</style>
