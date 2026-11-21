<script setup lang="ts">
import type { ChartSliderPosition, PairHistory, Trade } from '@/types';

const props = withDefaults(
  defineProps<{
    trades?: Trade[];
    availablePairs: string[];
    timeframe: string;
    historicView?: boolean;
    /** Reload data on pair switch if in historic view */
    reloadDataOnSwitch?: boolean;
    strategy?: string;
    sliderPosition?: ChartSliderPosition;
  }>(),
  {
    trades: () => [],
    historicView: false,
    reloadDataOnSwitch: false,
    strategy: '',
    sliderPosition: undefined,
  },
);

const emit = defineEmits<{
  refreshData: [pair: string, columns: string[]];
}>();

const settingsStore = useSettingsStore();
const botStore = useBotStore();
const plotStore = usePlotConfigStore();

const dataset = computed((): PairHistory => {
  const firstpair = botStore.activeBot.plotMultiPairs[0];
  if (props.historicView) {
    return botStore.activeBot.history[`${firstpair}__${props.timeframe}`]?.data;
  }
  return botStore.activeBot.candleData[`${firstpair}__${props.timeframe}`]?.data;
});

const datasetColumns = computed(() =>
  dataset.value ? (dataset.value.all_columns ?? dataset.value.columns) : [],
);

const strategyName = computed(() => props.strategy || dataset.value?.strategy || '');

const showPlotConfigModal = ref(false);
function showConfigurator() {
  showPlotConfigModal.value = !showPlotConfigModal.value;
}

const isSinglePairView = computed(() => botStore.activeBot.plotMultiPairs.length === 1);

watch(
  () => botStore.activeBot.selectedPair,
  () => {
    botStore.activeBot.plotMultiPairs = [botStore.activeBot.selectedPair];
  },
);

onMounted(() => {
  if (botStore.activeBot.selectedPair) {
    botStore.activeBot.plotMultiPairs = [botStore.activeBot.selectedPair];
  } else if (props.availablePairs.length > 0) {
    assignFirstPair();
  }
  plotStore.plotConfigChanged();
});

function refresh() {
  for (const pair of botStore.activeBot.plotMultiPairs) {
    emit('refreshData', pair, plotStore.usedColumns);
  }
}

function refreshIfNecessary(newValue: string[], oldValue: string[] | undefined) {
  for (const pair of newValue) {
    if (oldValue?.includes(pair)) {
      continue;
    }
    emit('refreshData', pair, plotStore.usedColumns);
  }
}

function assignFirstPair() {
  const [firstPair] = props.availablePairs;
  if (firstPair) {
    botStore.activeBot.plotMultiPairs = [firstPair];
  }
}

watch(
  () => props.availablePairs,
  () => {
    if (
      botStore.activeBot.plotMultiPairs.length === 0 ||
      botStore.activeBot.plotMultiPairs.some((p) => !props.availablePairs.includes(p))
    ) {
      assignFirstPair();
      refresh();
    }
  },
);

watch(
  () => botStore.activeBot.plotMultiPairs,
  (newValue, oldValue) => {
    if (newValue.length === 0) return;

    if (!props.historicView || props.reloadDataOnSwitch) {
      refreshIfNecessary(newValue, oldValue);
    }
  },
  {
    immediate: true,
  },
);

watch(
  () => settingsStore.multiPairSelection,
  () => {
    if (
      !settingsStore.multiPairSelection &&
      botStore.activeBot.plotMultiPairs.length > 1 &&
      botStore.activeBot.plotMultiPairs[0]
    ) {
      // Select only the first pair if switching to single pair mode
      botStore.activeBot.plotMultiPairs = [botStore.activeBot.plotMultiPairs[0]];
    }
  },
);

const singlePairSelection = computed({
  get() {
    return botStore.activeBot.plotMultiPairs[0] || '';
  },
  set(value: string) {
    botStore.activeBot.plotMultiPairs = [value];
  },
});
</script>

<template>
  <div class="flex h-full">
    <div class="flex-fill w-full flex-col align-items-stretch flex h-full">
      <div class="ft-cc-bar">
        <span class="ft-cc-strat ft-mono">{{ strategyName }} | {{ timeframe || '' }}</span>
        <MultiSelect
          v-if="settingsStore.multiPairSelection"
          v-model="botStore.activeBot.plotMultiPairs"
          class="ft-cc-pair"
          :options="availablePairs"
          optionlabel=""
          placeholder="Select pairs to plot"
          size="small"
          filter
        >
        </MultiSelect>
        <Select
          v-else
          v-model="singlePairSelection"
          class="ft-cc-pair"
          :options="availablePairs"
          size="small"
          :clearable="false"
          @input="refresh"
        >
        </Select>

        <Button
          title="Refresh chart"
          severity="secondary"
          :disabled="botStore.activeBot.plotMultiPairs.length === 0"
          size="small"
          @click="refresh"
        >
          <i-mdi-refresh />
        </Button>
        <BaseCheckbox v-model="settingsStore.multiPairSelection">
          <span class="text-nowrap">Multi pair</span>
        </BaseCheckbox>
        <div class="ft-cc-bar-right">
          <BaseCheckbox v-model="settingsStore.showMarkArea">
            <span class="text-nowrap">Show Chart Areas</span>
          </BaseCheckbox>
          <BaseCheckbox v-model="settingsStore.useHeikinAshiCandles">
            <span class="text-nowrap">Heikin Ashi</span>
          </BaseCheckbox>

          <PlotConfigSelect></PlotConfigSelect>

          <div>
            <Button
              size="small"
              title="Plot configurator"
              severity="secondary"
              @click="showConfigurator"
            >
              <template #icon>
                <i-mdi-cog />
              </template>
            </Button>
          </div>
        </div>
      </div>
      <div
        v-if="botStore.activeBot.plotMultiPairs?.length > 0"
        :class="{
          'min-w-0 w-full h-full ': isSinglePairView,
          'grid grid-cols-1 lg:grid-cols-2': !isSinglePairView,
        }"
      >
        <SingleCandleChartContainer
          v-for="pair in botStore.activeBot.plotMultiPairs"
          :key="pair"
          :available-pairs="availablePairs"
          :pair="pair"
          :historic-view="botStore.activeBot.isWebserverMode"
          :timeframe="timeframe"
          :trades="props.trades"
          :slider-position="props.sliderPosition"
          :is-single-pair-view="isSinglePairView"
          @refresh-data="refresh()"
        >
        </SingleCandleChartContainer>
      </div>
      <div v-else class="flex flex-col items-center justify-center h-full w-full">
        <FtEmpty title="No pair selected" />
      </div>
    </div>
    <Dialog
      id="plotConfiguratorModal"
      v-model:visible="showPlotConfigModal"
      header="Plot Configurator"
      ok-only
      hide-backdrop
    >
      <PlotConfigurator :is-visible="showPlotConfigModal" :columns="datasetColumns" />
    </Dialog>
  </div>
</template>

<style scoped>
.ft-cc-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 10px;
  padding: 0 6px 6px;
}
.ft-cc-strat {
  font-size: 12px;
  color: var(--ft-text-2);
  white-space: nowrap;
}
.ft-cc-pair {
  width: 220px;
  max-width: 100%;
}
.ft-cc-bar-right {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 12px;
  margin-left: auto;
}
</style>
