<script setup lang="ts">
const botStore = useBotStore();
const bot = computed(() => botStore.activeBot);
</script>

<template>
  <div class="ft-stack">
    <FtPanel
      v-if="bot.detailTradeId && bot.tradeDetail"
      :title="`Trade #${bot.tradeDetail.trade_id} · ${bot.tradeDetail.pair}`"
    >
      <template #actions>
        <Button size="small" severity="secondary" label="Close" @click="bot.setDetailTrade(null)" />
      </template>
      <TradeDetail :trade="bot.tradeDetail" :stake-currency="bot.stakeCurrency" />
    </FtPanel>

    <FtPanel title="Closed trades" flush>
      <template #actions>
        <span class="ft-hint">Click a trade for details.</span>
        <Button
          size="small"
          severity="secondary"
          title="Reload trades"
          aria-label="Reload trades"
          @click="bot.getTrades()"
        >
          <template #icon><i-mdi-refresh /></template>
        </Button>
      </template>
      <TradeList
        class="trade-history"
        :trades="bot.closedTrades"
        show-filter
        :rows="25"
        empty-text="No closed trades so far."
      />
    </FtPanel>

    <FtPanel title="Open trades" flush>
      <TradeList :trades="bot.openTrades" active-trades empty-text="Currently no open trades." />
    </FtPanel>

    <FtPanel title="Recent activity" flush>
      <RecentActivity :trades="bot.allTrades" :limit="10" />
    </FtPanel>
  </div>
</template>
