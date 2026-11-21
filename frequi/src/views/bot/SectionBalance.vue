<script setup lang="ts">
import type { WalletHistoryPerBot } from '@/types';

const botStore = useBotStore();
const bot = computed(() => botStore.activeBot);

const walletData = computed<WalletHistoryPerBot>(() =>
  bot.value.balanceHistory ? { [bot.value.botId]: bot.value.balanceHistory } : {},
);
const bal = computed(() => bot.value.balance);
</script>

<template>
  <div class="ft-stack">
    <FtTiles>
      <FtTile
        label="Bot balance"
        :value="bal?.total_bot !== undefined ? formatPrice(bal.total_bot, 2) : '-'"
        :sub="bal?.stake ?? ''"
        hint="Balance owned by the bot, in stake currency"
      />
      <FtTile
        label="Account balance"
        :value="bal?.total !== undefined ? formatPrice(bal.total, 2) : '-'"
        :sub="bal?.stake ?? ''"
        hint="Total account balance, in stake currency"
      />
      <FtTile
        label="Starting capital"
        :value="bal?.starting_capital !== undefined ? formatPrice(bal.starting_capital, 2) : '-'"
        :sub="bal?.stake ?? ''"
      />
      <FtTile
        label="Change"
        :value="
          bal?.starting_capital_ratio !== undefined
            ? formatSignedPercent(bal.starting_capital_ratio, 2)
            : '-'
        "
        :profit="bal?.starting_capital_ratio"
        sub="vs. starting capital"
      />
      <FtTile
        v-if="bal?.symbol"
        :label="`Value in ${bal.symbol}`"
        :value="formatPrice(bal.value_bot ?? bal.value, 2)"
        :sub="bot.botState?.dry_run ? 'dry-run' : 'live'"
      />
    </FtTiles>
    <FtPanel title="Balance per currency" flush>
      <BotBalance />
    </FtPanel>
    <FtPanel title="Balance history" flush body-height="320px">
      <WalletHistoryChart :wallet-data="walletData" :show-title="false" />
    </FtPanel>
  </div>
</template>
