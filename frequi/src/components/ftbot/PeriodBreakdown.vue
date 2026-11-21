<script setup lang="ts">
import { TimeSummaryOptions } from '@/types';

const botStore = useBotStore();
const settingsStore = useSettingsStore();

const props = withDefaults(
  defineProps<{
    multiBotView?: boolean;
    /** Show the table below the chart (single bot only) */
    showTable?: boolean;
  }>(),
  { multiBotView: false, showTable: false },
);

const hasWeekly = computed(
  () => botStore.activeBot?.botFeatures?.weeklyMonthlyStats || props.multiBotView,
);

const periodicBreakdownSelections = computed(() => {
  const vals = [{ value: TimeSummaryOptions.daily, text: 'Days' }];
  if (hasWeekly.value) {
    vals.push({ value: TimeSummaryOptions.weekly, text: 'Weeks' });
    vals.push({ value: TimeSummaryOptions.monthly, text: 'Months' });
  }
  return vals;
});

const absRelSelections = ref([
  { value: 'abs_profit', text: 'Absolute' },
  { value: 'rel_profit', text: 'Relative %' },
]);

const selectedStats = computed(() => {
  if (props.multiBotView) {
    switch (settingsStore.timeProfitPeriod) {
      case TimeSummaryOptions.weekly:
        return botStore.allWeeklyStatsSelectedBots;
      case TimeSummaryOptions.monthly:
        return botStore.allMonthlyStatsSelectedBots;
      default:
        return botStore.allDailyStatsSelectedBots;
    }
  }

  switch (settingsStore.timeProfitPeriod) {
    case TimeSummaryOptions.weekly:
      return botStore.activeBot.weeklyStats;
    case TimeSummaryOptions.monthly:
      return botStore.activeBot.monthlyStats;
    default:
      return botStore.activeBot.dailyStats;
  }
});

const selectedStatsSorted = computed(() => {
  // Sorted version for chart
  return {
    ...selectedStats.value,
    data: selectedStats.value.data
      ? Object.values(selectedStats.value.data).sort((a, b) => (a.date > b.date ? 1 : -1))
      : [],
  };
});

function refreshSummary() {
  if (props.multiBotView) {
    botStore.allGetTimeSummary(settingsStore.timeProfitPeriod);
  } else {
    botStore.activeBot.getTimeSummary(settingsStore.timeProfitPeriod);
  }
}

onMounted(() => {
  refreshSummary();
});
</script>

<template>
  <div class="ft-period">
    <div class="ft-period-bar">
      <SelectButton
        v-if="hasWeekly"
        v-model="settingsStore.timeProfitPeriod"
        :options="periodicBreakdownSelections"
        aria-label="Period"
        size="small"
        :allow-empty="false"
        option-label="text"
        option-value="value"
        @change="refreshSummary"
      ></SelectButton>
      <SelectButton
        v-model="settingsStore.timeProfitPreference"
        aria-label="Profit display"
        size="small"
        :allow-empty="false"
        option-label="text"
        option-value="value"
        :options="absRelSelections"
      >
      </SelectButton>
      <Button
        severity="secondary"
        size="small"
        class="ms-auto"
        title="Refresh"
        aria-label="Refresh"
        @click="refreshSummary"
      >
        <template #icon><i-mdi-refresh /></template>
      </Button>
    </div>

    <div
      v-if="
        !props.multiBotView ||
        botStore.selectedBotCount <= 1 ||
        settingsStore.timeProfitPreference !== 'rel_profit'
      "
      class="ft-period-chart"
    >
      <TimePeriodChart
        v-if="selectedStats && selectedStats.data"
        :daily-stats="selectedStatsSorted"
        :show-title="false"
        :profit-col="settingsStore.timeProfitPreference"
      />
    </div>
    <FtEmpty
      v-else
      class="ft-period-chart"
      text="Relative profit is only available when a single bot is selected. Switch to absolute profit."
    />
    <div v-if="!props.multiBotView && showTable" class="ft-period-table">
      <DataTable size="small" :value="selectedStats.data" scrollable>
        <template #empty>No data.</template>
        <Column field="date" header="Period" class="ft-mono"></Column>
        <Column
          field="abs_profit"
          :header="`Profit ${botStore.activeBot.stakeCurrency}`"
          class="ft-num"
        >
          <template #body="{ data, field }">
            <span :class="profitClass(data[field as string])">{{
              formatSigned(data[field as string], botStore.activeBot.stakeCurrencyDecimals)
            }}</span>
          </template>
        </Column>
        <Column
          field="fiat_value"
          :header="`In ${botStore.activeBot.dailyStats.fiat_display_currency ?? 'fiat'}`"
          class="ft-num"
        >
          <template #body="{ data, field }">
            {{ formatSigned(data[field as string], 2) }}
          </template>
        </Column>
        <Column
          v-if="botStore.activeBot.botFeatures.advancedDailyMetrics"
          field="rel_profit"
          header="Profit %"
          class="ft-num"
        >
          <template #body="{ data, field }">
            <span :class="profitClass(data[field as string])">{{
              formatSignedPercent(data[field as string], 2)
            }}</span>
          </template>
        </Column>
        <Column field="trade_count" header="Trades" class="ft-num"></Column>
      </DataTable>
    </div>
  </div>
</template>

<style scoped>
.ft-period {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-width: 0;
}
.ft-period-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}
.ft-period-chart {
  flex: 1 1 auto;
  min-height: 220px;
}
.ft-period-table {
  margin: 12px -18px -16px;
  border-top: 1px solid var(--ft-border);
}
@media (max-width: 700px) {
  .ft-period-table {
    margin: 12px -12px -12px;
  }
}
</style>
