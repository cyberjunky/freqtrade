<script setup lang="ts">
import { TimeSummaryOptions } from '@/types';

const botStore = useBotStore();
const bot = computed(() => botStore.activeBot);

onMounted(() => {
  if (bot.value.isBotOnline) {
    bot.value.getTimeSummary(TimeSummaryOptions.daily, { timescale: 30 }).catch(() => undefined);
  }
});

const cur = computed(() => bot.value.stakeCurrency);
const dec = computed(() => bot.value.stakeCurrencyDecimals);
const open = computed(() => sumOpenProfit(bot.value.openTrades));
const profit = computed(() => bot.value.profit);
const today = computed(() => profitToday(bot.value));
const maxOpen = computed(() => {
  const m = Number(bot.value.botState?.max_open_trades);
  return Number.isFinite(m) && m > 0 ? String(m) : 'unlimited';
});
const winRate = computed(() => {
  const w = profit.value?.winning_trades ?? 0;
  const l = profit.value?.losing_trades ?? 0;
  return w + l > 0 ? w / (w + l) : undefined;
});
const balance = computed(() => bot.value.balance?.total_bot ?? bot.value.balance?.total);
</script>

<template>
  <div class="ft-stack">
    <FtTiles>
      <FtTile label="Open trades" :value="bot.openTradeCount" :sub="`of ${maxOpen} slots`" />
      <FtTile
        label="Open P&L"
        :value="formatSigned(open.abs, dec)"
        :profit="open.abs"
        :sub="
          open.ratio !== undefined
            ? `${formatSignedPercent(open.ratio)} · unrealised`
            : `${cur} unrealised`
        "
        hint="Open profit (unrealised) of all open trades"
      />
      <FtTile
        label="P&L today"
        :value="today !== undefined ? formatSigned(today, dec) : '-'"
        :profit="today"
        :sub="`${cur} closed today`"
      />
      <FtTile
        label="Closed P&L"
        :value="profit ? formatSigned(profit.profit_closed_coin, dec) : '-'"
        :profit="profit?.profit_closed_coin"
        :sub="
          profit
            ? `${formatSignedPercent(profit.profit_closed_ratio)} · realised`
            : `${cur} realised`
        "
        hint="Closed profit (realised), ratio against the starting balance"
      />
      <FtTile
        label="Win rate"
        :value="winRate !== undefined ? formatPercent(winRate, 1) : '-'"
        :sub="`${profit?.winning_trades ?? 0} W / ${profit?.losing_trades ?? 0} L`"
      />
      <FtTile
        label="Balance"
        :value="balance !== undefined ? formatPrice(balance, 2) : '-'"
        :sub="`${cur} · ${bot.botState?.dry_run ? 'dry-run' : 'live'}`"
      />
      <FtTile
        label="Profit factor"
        :value="profit?.profit_factor ? formatNumber(profit.profit_factor, 2) : '-'"
        :sub="
          profit?.expectancy !== undefined ? `expectancy ${formatNumber(profit.expectancy, 2)}` : ''
        "
      />
      <FtTile
        label="Max drawdown"
        :value="profit?.max_drawdown ? formatPercent(profit.max_drawdown, 2) : '-'"
        :sub="profit?.max_drawdown_abs ? `${formatPrice(profit.max_drawdown_abs, dec)} ${cur}` : ''"
      />
    </FtTiles>

    <div class="ft-grid-2">
      <FtPanel title="Cumulative profit" flush body-height="300px">
        <CumProfitChart
          v-if="bot.trades.length || bot.openTrades.length"
          :trades="bot.trades"
          :open-trades="bot.openTrades"
          :show-title="false"
        />
        <FtEmpty v-else title="No trades yet" />
      </FtPanel>
      <FtPanel title="Profit per day" body-height="300px">
        <PeriodBreakdown />
      </FtPanel>
    </div>

    <FtPanel title="Trade profits" flush body-height="260px">
      <TradesLogChart v-if="bot.trades.length" :trades="bot.trades" :show-title="false" />
      <FtEmpty v-else title="No closed trades yet" />
    </FtPanel>

    <FtPanel title="Open trades" flush>
      <template #actions>
        <span class="ft-hint">Click a trade for details.</span>
      </template>
      <TradeList
        class="open-trades"
        :trades="bot.openTrades"
        active-trades
        empty-text="Currently no open trades."
      />
    </FtPanel>

    <FtPanel
      v-if="bot.detailTradeId && bot.tradeDetail"
      :title="`Trade #${bot.tradeDetail.trade_id} · ${bot.tradeDetail.pair}`"
    >
      <template #actions>
        <Button size="small" severity="secondary" label="Close" @click="bot.setDetailTrade(null)" />
      </template>
      <TradeDetail :trade="bot.tradeDetail" :stake-currency="bot.stakeCurrency" />
    </FtPanel>
  </div>
</template>
