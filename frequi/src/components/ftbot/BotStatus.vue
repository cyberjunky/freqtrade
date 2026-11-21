<script setup lang="ts">
/** Status and configuration of the active bot as key / value rows. */
const botStore = useBotStore();
const bot = computed(() => botStore.activeBot);
const state = computed(() => bot.value.botState);
const profit = computed(() => bot.value.profit);
</script>

<template>
  <dl v-if="state" class="ft-kv">
    <dt>State</dt>
    <dd><FtState :state="botUiState(bot)" /></dd>
    <dt>Mode</dt>
    <dd><FtMode :mode="botUiMode(bot)" /></dd>
    <dt>Freqtrade version</dt>
    <dd>{{ bot.version || 'N/A' }}</dd>
    <dt>API version</dt>
    <dd>{{ formatNumber(bot.botApiVersion, 2) }}</dd>
    <dt>Bot name</dt>
    <dd>{{ state.bot_name || bot.uiBotName }}</dd>
    <dt>Strategy</dt>
    <dd>
      {{ state.strategy || 'N/A' }}
      <span v-if="state.strategy_version" class="ft-dim">v{{ state.strategy_version }}</span>
    </dd>
    <dt>Exchange</dt>
    <dd>{{ state.exchange }} {{ state.demo_trading ? '(demo)' : '' }}</dd>
    <dt>Market</dt>
    <dd>
      {{ state.trading_mode || 'spot' }}
      {{ state.trading_mode !== 'spot' ? (state.margin_mode ?? '') : '' }}
    </dd>
    <dt>Timeframe</dt>
    <dd>{{ state.timeframe || 'N/A' }}</dd>
    <dt>Stake currency</dt>
    <dd>{{ state.stake_currency }}</dd>
    <template v-if="profit">
      <template v-if="profit.bot_start_timestamp">
        <dt>Bot started</dt>
        <dd><DateTimeTZ :date="profit.bot_start_timestamp" show-timezone /></dd>
      </template>
      <template v-if="profit.first_trade_timestamp">
        <dt>First trade opened</dt>
        <dd><DateTimeTZ :date="profit.first_trade_timestamp" show-timezone /></dd>
        <dt>Latest trade opened</dt>
        <dd><DateTimeTZ :date="profit.latest_trade_timestamp" show-timezone /></dd>
      </template>
      <dt>Trades</dt>
      <dd>{{ profit.trade_count ?? 0 }} ({{ profit.closed_trade_count ?? 0 }} closed)</dd>
      <dt>Average duration</dt>
      <dd>{{ profit.avg_duration || 'N/A' }}</dd>
      <dt>Best pair</dt>
      <dd>
        {{ profit.best_pair || 'N/A' }}
        <span v-if="profit.best_pair" :class="profitClass(profit.best_pair_profit_ratio)">{{
          formatSignedPercent(profit.best_pair_profit_ratio, 2)
        }}</span>
      </dd>
      <template v-if="profit.trading_volume">
        <dt>Trading volume</dt>
        <dd>
          {{
            formatPriceCurrency(
              profit.trading_volume,
              state.stake_currency,
              state.stake_currency_decimals ?? 3,
            )
          }}
        </dd>
      </template>
    </template>
  </dl>
</template>
