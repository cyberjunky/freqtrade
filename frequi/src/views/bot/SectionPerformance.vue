<script setup lang="ts">
const botStore = useBotStore();
const bot = computed(() => botStore.activeBot);
</script>

<template>
  <div class="ft-stack">
    <div class="ft-grid-2">
      <FtPanel title="Performance" flush>
        <BotPerformance />
      </FtPanel>
      <FtPanel title="Daily / weekly / monthly">
        <PeriodBreakdown show-table />
      </FtPanel>
    </div>
    <div class="ft-grid-2">
      <FtPanel title="Profit distribution" flush body-height="320px">
        <ProfitDistributionChart :trades="bot.trades" :show-title="false" />
      </FtPanel>
      <FtPanel title="Statistics" flush>
        <BotProfit
          v-if="bot.profitAll"
          :profit-all="bot.profitAll"
          :stake-currency="bot.botState.stake_currency ?? 'USDT'"
          :stake-currency-decimals="bot.botState.stake_currency_decimals ?? 3"
        />
        <FtEmpty v-else title="No statistics available" />
      </FtPanel>
    </div>
  </div>
</template>
