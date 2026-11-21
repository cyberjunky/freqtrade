<script setup lang="ts">
import type { ClosedTrade } from '@/types';
import TradeDurationChart from '../charts/TradeDurationChart.vue';

defineProps<{
  trades: ClosedTrade[];
}>();

const botStore = useBotStore();

const { state: marketChangeData } = useAsyncState(
  () => botStore.activeBot.getBacktestMarketChange(),
  null,
);

const { state: walletData } = useAsyncState(
  () => botStore.activeBot.getBacktestWalletChange(),
  null,
);
</script>
<template>
  <div class="ft-grid-2">
    <FtPanel title="Trade profits" flush body-height="320px">
      <TradesLogChart :trades="trades" :show-title="false" />
    </FtPanel>
    <FtPanel title="Trade durations" flush body-height="320px">
      <TradeDurationChart :trades="trades" :show-title="false" />
    </FtPanel>
    <FtPanel title="Cumulative profit" flush body-height="320px">
      <CumProfitChart :trades="trades" :show-title="false" />
    </FtPanel>
    <FtPanel v-if="walletData" title="Wallet balance" flush body-height="320px">
      <WalletHistoryChart :wallet-data="walletData" :show-title="false" />
    </FtPanel>
    <FtPanel v-if="marketChangeData" title="Market change" flush body-height="320px">
      <MarketChangeChart :market-change-data="marketChangeData" />
    </FtPanel>
    <FtPanel title="Profit distribution" flush body-height="320px">
      <ProfitDistributionChart :trades="trades" :show-title="false" />
    </FtPanel>
  </div>
</template>
