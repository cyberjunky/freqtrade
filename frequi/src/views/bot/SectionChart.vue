<script setup lang="ts">
import { MarginMode, TradingMode } from '@/types';
import type { ExchangeSelection, Markets, MarketsPayload, PairHistoryPayload } from '@/types';

const botStore = useBotStore();
const chartStore = useChartConfigStore();

const bot = computed(() => botStore.activeBot);

const finalTimeframe = computed<string>(() => {
  return bot.value.isWebserverMode
    ? chartStore.selectedTimeframe || bot.value.strategy?.timeframe || ''
    : bot.value.timeframe;
});

const exchange = ref<{
  customExchange: boolean;
  selectedExchange: ExchangeSelection;
}>({
  customExchange: false,
  selectedExchange: {
    exchange: bot.value.botState.exchange,
    trade_mode: {
      margin_mode: MarginMode.NONE,
      trading_mode: TradingMode.SPOT,
    },
  },
});

const markets = ref<Markets | null>(null);

const availablePairs = computed<string[]>(() => {
  if (bot.value.isWebserverMode) {
    if (chartStore.useLiveData) {
      return Object.keys(markets.value?.markets || {}).sort() || [];
    }
    if (finalTimeframe.value && finalTimeframe.value !== '') {
      const tf = finalTimeframe.value;
      return bot.value.pairlistWithTimeframe
        .filter(([, timeframe]) => timeframe === tf)
        .map(([pair]) => pair);
    }
    return bot.value.pairlist;
  }
  return bot.value.whitelist;
});

onMounted(() => {
  if (bot.value.isWebserverMode) {
    // Get available pairs for all timeframes
    bot.value.getAvailablePairs({});
  } else if (!bot.value.whitelist || bot.value.whitelist.length === 0) {
    bot.value.getWhitelist();
  }
});

function refreshOHLCV(pair: string, columns: string[]) {
  if (bot.value.isWebserverMode && finalTimeframe.value) {
    const payload: PairHistoryPayload = {
      pair: pair,
      timeframe: finalTimeframe.value,
      timerange: chartStore.timerange,
      strategy: chartStore.strategy,
      columns: columns,
      live_mode: chartStore.useLiveData,
    };
    if (exchange.value.customExchange) {
      payload.exchange = exchange.value.selectedExchange.exchange;
      payload.trading_mode = exchange.value.selectedExchange.trade_mode.trading_mode;
      payload.margin_mode = exchange.value.selectedExchange.trade_mode.margin_mode;
    }
    bot.value.getPairHistory(payload);
  } else {
    bot.value.getPairCandles({
      pair: pair,
      timeframe: finalTimeframe.value,
      columns: columns,
    });
  }
}

watch(
  () => chartStore.useLiveData,
  async () => {
    if (bot.value.isWebserverMode && chartStore.useLiveData) {
      const payload: MarketsPayload = {};
      if (exchange.value.customExchange) {
        payload.exchange = exchange.value.selectedExchange.exchange;
        payload.trading_mode = exchange.value.selectedExchange.trade_mode.trading_mode;
        payload.margin_mode = exchange.value.selectedExchange.trade_mode.margin_mode;
      }

      markets.value = await bot.value.getMarkets(payload);
    }
  },
  {
    immediate: true,
  },
);

const showPairs = ref(true);
</script>

<template>
  <div class="ft-stack">
    <FtPanel v-if="bot.isWebserverMode" title="Data source">
      <div class="ft-src-grid">
        <div>
          <span class="ft-label">Strategy</span>
          <StrategySelect v-model="chartStore.strategy"></StrategySelect>
          <BaseCheckbox
            v-if="bot.botFeatures.chartLiveData"
            v-model="chartStore.useLiveData"
            class="mt-2"
            title="Use live data from the exchange. Only use if you don't have data downloaded locally."
          >
            Use live data
          </BaseCheckbox>
        </div>
        <div>
          <span class="ft-label">Timeframe</span>
          <TimeframeSelect v-model="chartStore.selectedTimeframe" />
        </div>
        <TimeRangeSelect v-model="chartStore.timerange"></TimeRangeSelect>
        <div>
          <BaseCheckbox v-model="exchange.customExchange">Custom exchange</BaseCheckbox>
          <span v-show="!exchange.customExchange" class="ft-hint">
            Current exchange: {{ bot.botState.exchange }} {{ bot.botState.trading_mode }}
          </span>
          <ExchangeSelect v-show="exchange.customExchange" v-model="exchange.selectedExchange" />
        </div>
      </div>
    </FtPanel>

    <div class="ft-chart-layout" :class="{ 'has-pairs': !bot.isWebserverMode && showPairs }">
      <FtPanel v-if="!bot.isWebserverMode && showPairs" title="Pairs" class="ft-chart-pairs">
        <PairSummary
          :pairlist="bot.whitelist"
          :current-locks="bot.activeLocks"
          :trades="bot.openTrades"
        />
      </FtPanel>
      <FtPanel title="Chart" flush class="ft-chart-panel">
        <template #actions>
          <Button
            v-if="!bot.isWebserverMode"
            size="small"
            severity="secondary"
            :label="showPairs ? 'Hide pairs' : 'Show pairs'"
            @click="showPairs = !showPairs"
          />
        </template>
        <div class="ft-chart-body">
          <CandleChartContainer
            :available-pairs="availablePairs"
            :historic-view="bot.isWebserverMode"
            :timeframe="finalTimeframe"
            :trades="bot.allTrades"
            :timerange="bot.isWebserverMode ? chartStore.timerange : undefined"
            :strategy="bot.isWebserverMode ? chartStore.strategy : undefined"
            @refresh-data="refreshOHLCV"
          >
          </CandleChartContainer>
        </div>
      </FtPanel>
    </div>
  </div>
</template>

<style scoped>
.ft-src-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr));
  gap: 14px 18px;
  align-items: start;
}
.ft-chart-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--ft-gap);
  align-items: start;
}
.ft-chart-layout.has-pairs {
  grid-template-columns: 250px minmax(0, 1fr);
}
.ft-chart-pairs {
  max-height: calc(100dvh - 250px);
  min-height: 300px;
  overflow: auto;
}
.ft-chart-body {
  height: calc(100dvh - 300px);
  min-height: 480px;
  padding: 8px 6px 4px;
}
@media (max-width: 1000px) {
  .ft-chart-layout.has-pairs {
    grid-template-columns: minmax(0, 1fr);
  }
  .ft-chart-pairs {
    max-height: 260px;
    min-height: 0;
    order: 2;
  }
  .ft-chart-body {
    height: 70dvh;
    min-height: 420px;
  }
}
</style>
