<script setup lang="ts">
enum BtRunModes {
  run = 'run',
  results = 'results',
  visualize = 'visualize',
  visualizesummary = 'visualize-summary',
  compareresults = 'compare-results',
  historicresults = 'historicResults',
}

const botStore = useBotStore();
const btStore = useBtStore();

const bot = computed(() => botStore.activeBotorUndefined);

const hasBacktestResult = computed(() =>
  bot.value?.backtestHistory ? Object.keys(bot.value.backtestHistory).length !== 0 : false,
);
const hasMultiBacktestResult = computed(() =>
  bot.value?.backtestHistory ? Object.keys(bot.value.backtestHistory).length > 1 : false,
);

const timeframe = computed((): string => {
  return bot.value?.selectedBacktestResult?.timeframe ?? '';
});

const btFormMode = ref<BtRunModes>(BtRunModes.run);
const pollInterval = ref<number | null>(null);

function selectBacktestResult() {
  const result = bot.value?.selectedBacktestResult;
  if (!bot.value || !result) {
    return;
  }
  // Set parameters for this result
  btStore.strategy = result.strategy_name;
  bot.value.getStrategy(btStore.strategy);
  btStore.selectedTimeframe = result.timeframe;
  btStore.selectedDetailTimeframe = result.timeframe_detail || '';
  // TODO: maybe this should not use timerange, but the actual backtest start/end results instead?
  btStore.timerange = result.timerange;
  btStore.enableProtections = result.enable_protections;
}

watch(
  () => bot.value?.selectedBacktestResultKey,
  () => {
    selectBacktestResult();
  },
);

onMounted(() => bot.value?.getState());

function stopPolling() {
  if (pollInterval.value) {
    clearInterval(pollInterval.value);
    pollInterval.value = null;
  }
}
watch(
  () => bot.value?.backtestRunning,
  () => {
    if (bot.value?.backtestRunning === true) {
      stopPolling();
      pollInterval.value = window.setInterval(() => bot.value?.pollBacktest(), 1000);
    } else {
      stopPolling();
    }
  },
);
onBeforeUnmount(stopPolling);
</script>

<template>
  <ToolPage
    title="Backtesting"
    description="Run backtests, load stored results and analyze them."
    requires-webserver
  >
    <template v-if="bot">
      <div class="ft-bt-layout" :class="{ 'has-results': hasBacktestResult }">
        <FtPanel v-if="hasBacktestResult" title="Loaded results" class="ft-bt-results">
          <BacktestResultSelect
            :backtest-history="bot.backtestHistory"
            :selected-backtest-result-key="bot.selectedBacktestResultKey"
            :can-use-modify="bot.botFeatures.backtestSetNotes"
            @selection-change="bot.setBacktestResultKey"
            @remove-result="bot.removeBacktestResultFromMemory"
            @update-result="bot.saveBacktestResultMetadata"
          />
        </FtPanel>
        <div class="ft-bt-main">
          <Tabs v-model:value="btFormMode" lazy scrollable>
            <div class="ft-bt-tabs">
              <TabList>
                <Tab
                  v-if="bot.botFeatures.backtestHistory"
                  value="historicResults"
                  :disabled="!bot.canRunBacktest"
                  >Load results</Tab
                >
                <Tab value="run" :disabled="!bot.canRunBacktest">Run backtest</Tab>
                <Tab id="bt-analyze-btn" value="results" :disabled="!hasBacktestResult"
                  >Analyze result</Tab
                >
                <Tab
                  v-if="hasMultiBacktestResult"
                  value="compare-results"
                  :disabled="!hasMultiBacktestResult"
                  >Compare results</Tab
                >
                <Tab value="visualize-summary" :disabled="!hasBacktestResult"
                  >Visualize summary</Tab
                >
                <Tab value="visualize" :disabled="!hasBacktestResult">Visualize result</Tab>
              </TabList>
              <span v-show="bot.backtestRunning" class="ft-bt-running ft-mono" role="status">
                <i-mdi-loading class="ft-bt-spin" aria-hidden="true" />
                Backtest running: {{ bot.backtestStep }}
                {{ formatPercent(bot.backtestProgress, 2) }}
              </span>
            </div>
            <TabPanels>
              <TabPanel value="historicResults">
                <FtPanel title="Stored results" flush>
                  <BacktestHistoryLoad />
                </FtPanel>
              </TabPanel>
              <TabPanel value="run">
                <BacktestRun />
              </TabPanel>
              <TabPanel value="results">
                <BacktestResultAnalysis
                  v-if="hasBacktestResult && bot.selectedBacktestResult"
                  :backtest-result="bot.selectedBacktestResult"
                />
              </TabPanel>
              <TabPanel value="compare-results">
                <BacktestResultComparison
                  v-if="hasMultiBacktestResult"
                  :backtest-results="bot.backtestHistory"
                />
              </TabPanel>
              <TabPanel value="visualize-summary">
                <BacktestGraphs
                  v-if="hasBacktestResult && bot.selectedBacktestResult"
                  :trades="bot.selectedBacktestResult.trades"
                />
              </TabPanel>
              <TabPanel value="visualize">
                <BacktestResultChart
                  v-if="bot.selectedBacktestResult"
                  :timeframe="timeframe"
                  :strategy="btStore.strategy"
                  :timerange="btStore.timerange"
                  :backtest-result="bot.selectedBacktestResult"
                />
              </TabPanel>
            </TabPanels>
          </Tabs>
        </div>
      </div>
    </template>
  </ToolPage>
</template>

<style lang="css" scoped>
.ft-bt-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--ft-gap);
  align-items: start;
}
.ft-bt-layout.has-results {
  grid-template-columns: 300px minmax(0, 1fr);
}
.ft-bt-main {
  min-width: 0;
}
.ft-bt-tabs {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 16px;
}
.ft-bt-running {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--ft-warning);
}
.ft-bt-spin {
  animation: ft-bt-spin 0.9s linear infinite;
}
@keyframes ft-bt-spin {
  to {
    transform: rotate(360deg);
  }
}
@media (max-width: 1000px) {
  .ft-bt-layout.has-results {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
