<script setup lang="ts">
import ECharts from 'vue-echarts';

import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import {
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  TooltipComponent,
} from 'echarts/components';
import type { EChartsOption, LineSeriesOption } from 'echarts';

import type { SegmentedItem } from '@/components/ui/FtSegmented.vue';
import type { ClosedTrade, MarketReference, WalletHistoryPerBot } from '@/types';
import {
  type Point,
  closedPoints,
  equityPoints,
  marketDirection,
  marketStats,
  rebase,
  referenceSeries,
} from '@/utils/charts/botCompare';

use([
  LineChart,
  CanvasRenderer,
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  TooltipComponent,
]);

/**
 * All selected bots on one timeline, each starting at 0 at the first common point in the
 * visible window, with an optional market reference (basket or BTC) on the right axis.
 */
const props = defineProps<{
  walletData: WalletHistoryPerBot;
  trades: ClosedTrade[];
}>();

type Range = '7' | '30' | '90' | 'all';
type Unit = 'pct' | 'abs';
type Curve = 'open' | 'closed';
type RefMode = 'basket' | 'btc' | 'off';

const DAY = 86_400_000;
const botStore = useBotStore();
const settingsStore = useSettingsStore();

const range = ref<Range>('30');
const unit = ref<Unit>('pct');
const curve = ref<Curve>('open');
const refMode = ref<RefMode>('basket');

const rangeItems: SegmentedItem<Range>[] = [
  { value: '7', label: '7d' },
  { value: '30', label: '30d' },
  { value: '90', label: '90d' },
  { value: 'all', label: 'All' },
];
const curveItems: SegmentedItem<Curve>[] = [
  { value: 'open', label: 'Incl. open', title: 'Balance including open positions' },
  { value: 'closed', label: 'Closed only', title: 'Starting capital plus closed-trade profit' },
];
const refItems: SegmentedItem<RefMode>[] = [
  {
    value: 'basket',
    label: 'Basket',
    title: 'BTC ETH SOL XRP ADA DOGE LINK LTC, equal start weights',
  },
  { value: 'btc', label: 'BTC' },
  { value: 'off', label: 'Off' },
];

// ---- Bots -------------------------------------------------------------------
const bots = computed(() =>
  Object.entries(props.walletData)
    .map(([botId, history], idx) => {
      const store = botStore.botStores[botId];
      const equity = equityPoints(history);
      const first = equity[0];
      if (!first) return undefined;
      const capital = store?.balance?.starting_capital || first[1];
      const closed = closedPoints(
        props.trades.filter((t) => t.botId === botId),
        first[0],
        capital,
      );
      // Carry the last closed-profit level up to the latest snapshot.
      const lastClosed = closed[closed.length - 1]!;
      closed.push([Math.max(equity[equity.length - 1]![0], lastClosed[0]), lastClosed[1]]);
      return {
        botId,
        name: history.botName ?? botId,
        color: themeTokens.series[idx % Math.max(themeTokens.series.length, 1)],
        equity,
        closed,
        capital,
        currency: store?.stakeCurrency ?? '',
      };
    })
    .filter((b) => b !== undefined),
);

const sameCurrency = computed(() => new Set(bots.value.map((b) => b.currency)).size <= 1);
const effectiveUnit = computed<Unit>(() => (sameCurrency.value ? unit.value : 'pct'));
const unitItems = computed<SegmentedItem<Unit>[]>(() => [
  { value: 'pct', label: '%', title: 'Change in percent of starting capital' },
  {
    value: 'abs',
    label: bots.value[0]?.currency || 'Currency',
    disabled: !sameCurrency.value,
    title: sameCurrency.value ? 'Change in stake currency' : 'Bots use different currencies',
  },
]);

// ---- Visible window -----------------------------------------------------------
const now = ref(Date.now());
useIntervalFn(() => (now.value = Date.now()), 60_000);
const zoomWindow = ref<[number, number]>();
watch(range, () => (zoomWindow.value = undefined));

const dataStart = computed(() => Math.min(...bots.value.map((b) => b.equity[0]![0])));
const view = computed<[number, number]>(
  () =>
    zoomWindow.value ?? [
      range.value === 'all' ? dataStart.value : now.value - Number(range.value) * DAY,
      now.value,
    ],
);
/** First moment every bot has data, inside the window. */
const t0 = computed(() => Math.max(view.value[0], ...bots.value.map((b) => b.equity[0]![0])));

const chart = ref<InstanceType<typeof ECharts>>();
const onZoom = useDebounceFn(() => {
  const dz = (chart.value?.getOption() as EChartsOption | undefined)?.dataZoom;
  const z = Array.isArray(dz) ? dz[0] : dz;
  const start = Number(z?.startValue);
  const end = Number(z?.endValue);
  if (Number.isFinite(start) && Number.isFinite(end)) {
    zoomWindow.value = [start, end];
  }
}, 150);

// ---- Market reference ---------------------------------------------------------------
const reference = ref<MarketReference>();
const referenceError = ref('');
const referenceBot = computed(() =>
  botStore.selectedBots.find((b) => b.isBotOnline && b.botFeatures.marketReference),
);
const referenceDays = computed(() =>
  Number.isFinite(dataStart.value)
    ? Math.min(365, Math.max(7, Math.ceil((Date.now() - dataStart.value) / DAY) + 1))
    : 30,
);

async function loadReference() {
  const bot = referenceBot.value;
  if (!bot || refMode.value === 'off') return;
  try {
    reference.value = await bot.getMarketReference(referenceDays.value);
    referenceError.value = '';
  } catch {
    referenceError.value = `Market reference unavailable from ${bot.uiBotName}.`;
  }
}
watch([() => referenceBot.value?.botId, referenceDays, refMode], loadReference, {
  immediate: true,
});
useIntervalFn(loadReference, 15 * 60_000);

const referenceLines = computed(() =>
  reference.value ? referenceSeries(reference.value, t0.value) : undefined,
);
const stats = computed(() => (reference.value ? marketStats(reference.value) : undefined));
const referenceChange = computed(() =>
  refMode.value === 'btc' ? stats.value?.btc24h : stats.value?.basket24h,
);
const direction = computed(() => marketDirection(referenceChange.value));

// ---- Chart ------------------------------------------------------------------------
function fmt(value: number, pct: boolean): string {
  return pct ? `${formatSigned(value, 2)}%` : formatSigned(value, 2);
}

const option = computed<EChartsOption>(() => {
  const pct = effectiveUnit.value === 'pct';
  const series: LineSeriesOption[] = bots.value.map((b, i) => ({
    type: 'line',
    name: b.name,
    color: b.color,
    showSymbol: false,
    step: curve.value === 'closed' ? 'end' : undefined,
    yAxisIndex: 0,
    data: rebase(
      curve.value === 'closed' ? b.closed : b.equity,
      t0.value,
      pct ? b.capital : undefined,
    ),
    markLine:
      i === 0
        ? {
            symbol: 'none',
            silent: true,
            animation: false,
            label: { show: false },
            lineStyle: { type: 'solid', color: themeTokens['text-2'], width: 1, opacity: 0.5 },
            data: [{ yAxis: 0 }],
          }
        : undefined,
  }));

  const refOn = refMode.value !== 'off' && !!referenceLines.value;
  if (refOn) {
    const lines = referenceLines.value!;
    series.push({
      type: 'line',
      name: refMode.value === 'btc' ? 'BTC (right axis)' : `Basket ${lines.members} (right axis)`,
      color: themeTokens['text-2'],
      showSymbol: false,
      step: 'end',
      yAxisIndex: 1,
      lineStyle: { type: 'dashed', width: 1 },
      data: (refMode.value === 'btc' ? lines.btc : lines.basket).filter(
        ([t]) => t >= dataStart.value,
      ),
    });
  }

  return {
    backgroundColor: 'rgba(0, 0, 0, 0)',
    grid: { ...echartsGridDefault, top: 32, right: refOn ? 55 : 30 },
    legend: { type: 'scroll', top: 0, left: 10, right: 10 },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const list = (Array.isArray(params) ? params : [params]) as {
          marker: string;
          seriesName: string;
          seriesIndex: number;
          data: Point;
        }[];
        if (!list.length) return '';
        const lines = list.map(
          (p) =>
            `${p.marker}${p.seriesName}: ${fmt(p.data[1], pct || p.seriesIndex >= bots.value.length)}`,
        );
        return [timestampms(list[0]!.data[0]), ...lines].join('<br />');
      },
    },
    xAxis: { type: 'time', axisLine: { onZero: false } },
    yAxis: [
      {
        type: 'value',
        scale: true,
        splitLine: { show: false },
        axisLabel: { formatter: (v: number) => (pct ? `${v}%` : formatPrice(v, 2)) },
      },
      {
        type: 'value',
        scale: true,
        show: refOn,
        position: 'right',
        splitLine: { show: false },
        axisLabel: { formatter: '{value}%' },
      },
    ],
    dataZoom: [
      { type: 'inside', startValue: view.value[0], endValue: view.value[1] },
      { ...dataZoomPartial, bottom: 10, startValue: view.value[0], endValue: view.value[1] },
    ],
    series,
  };
});
</script>

<template>
  <div class="ft-compare">
    <div class="ft-compare-bar">
      <FtSegmented v-model="range" :items="rangeItems" label="Period" small />
      <Button
        v-if="zoomWindow"
        size="small"
        severity="secondary"
        label="Reset zoom"
        @click="zoomWindow = undefined"
      />
      <FtSegmented v-model="unit" :items="unitItems" label="Unit" small />
      <FtSegmented v-model="curve" :items="curveItems" label="Curve" small />
      <FtSegmented v-model="refMode" :items="refItems" label="Market reference" small />
    </div>

    <div v-if="stats && refMode !== 'off'" class="ft-compare-market">
      <span>
        {{ refMode === 'btc' ? 'BTC' : 'Basket' }} 24h
        <b :class="profitClass(referenceChange)">{{ formatSignedPercent(referenceChange) }}</b>
        <span v-if="direction" class="ft-hint">({{ direction }})</span>
      </span>
      <span v-if="refMode !== 'btc'">
        BTC 24h <b :class="profitClass(stats.btc24h)">{{ formatSignedPercent(stats.btc24h) }}</b>
      </span>
      <span>
        Rising <b>{{ stats.rising }} / {{ stats.members }}</b>
      </span>
      <span v-if="stats.vol24h !== undefined">
        Realised vol 24h <b>{{ formatPercent(stats.vol24h, 2) }}</b>
      </span>
      <span class="ft-hint">{{ reference?.exchange }} · {{ timestampms(stats.asOf) }}</span>
    </div>
    <div v-else-if="referenceError && refMode !== 'off'" class="ft-compare-market ft-hint">
      {{ referenceError }}
    </div>

    <div class="ft-compare-chart">
      <ECharts
        v-if="bots.length"
        ref="chart"
        :option="option"
        :theme="settingsStore.chartTheme"
        autoresize
        @datazoom="onZoom"
      />
      <FtEmpty v-else title="No balance history available">
        <span>The selected bots report no wallet history yet.</span>
      </FtEmpty>
    </div>
    <div class="ft-hint ft-compare-note">
      Every bot starts at 0 at the first moment all of them have data in the window. % is the change
      in percent of the bot's starting capital. Hours before a bot's wallet history was recorded are
      rebuilt from its trades and hourly candles.
    </div>
  </div>
</template>

<style scoped>
.ft-compare {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 6px;
  padding: 8px 10px;
}
.ft-compare-bar,
.ft-compare-market {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 14px;
}
.ft-compare-market {
  font-size: 12.5px;
}
.ft-compare-market b {
  font-family: var(--ft-font-mono);
  font-weight: 500;
}
.ft-compare-chart {
  flex: 1;
  min-height: 220px;
}
.ft-compare-note {
  font-size: 11.5px;
}
.echarts {
  height: 100%;
  width: 100%;
}
</style>
