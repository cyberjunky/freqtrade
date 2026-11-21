<script setup lang="ts">
import type { WalletHistoryPerBot } from '@/types';
import type { SegmentedItem } from '@/components/ui/FtSegmented.vue';
import type LoginModal from '@/components/LoginModal.vue';

type Scope = 'live' | 'dry' | 'all';

const botStore = useBotStore();
const loginModal = ref<InstanceType<typeof LoginModal>>();
const botFilter = ref('');

onMounted(() => {
  if (botStore.hasBots) {
    botStore.allGetDaily({ timescale: 30 });
  }
});

// ---- Scope ------------------------------------------------------------------
const scopeItems: SegmentedItem<Scope>[] = [
  { value: 'live', label: 'Live', title: 'Only bots trading real money' },
  { value: 'dry', label: 'Dry-run', title: 'Only simulated (dry-run) bots' },
  { value: 'all', label: 'All', title: 'All bots' },
];

/** Scope is derived from the selected bots, so manual (per row) selections show no active scope. */
const scope = computed<Scope | undefined>({
  get: () => {
    const all = botStore.allBotStores;
    if (all.length === 0) return 'all';
    if (all.every((b) => b.isSelected)) return 'all';
    const matches = (dry: boolean) =>
      all.some((b) => b.isSelected) &&
      all.every((b) => b.isSelected === (b.isBotOnline && !!b.botState?.dry_run === dry));
    if (matches(false)) return 'live';
    if (matches(true)) return 'dry';
    return undefined;
  },
  set: (val) => {
    if (val) {
      botStore.toggleBotsByState(val);
    }
  },
});

// ---- Aggregates over the selected bots ----------------------------------------
const selected = computed(() => botStore.selectedBots.filter((b) => !b.isWebserverMode));
const sameStake = computed(() => botStore.allSelectedBotsSameStake);
const currency = computed(() => (sameStake.value ? (selected.value[0]?.stakeCurrency ?? '') : ''));
const decimals = computed(() => selected.value[0]?.stakeCurrencyDecimals ?? 3);

const totals = computed(() => {
  let openTrades = 0;
  let maxOpen = 0;
  let maxKnown = true;
  let openAbs = 0;
  let closedAbs = 0;
  let today = 0;
  let todayKnown = false;
  let wins = 0;
  let losses = 0;
  let balance = 0;
  let live = 0;
  let dry = 0;
  let offline = 0;
  selected.value.forEach((bot) => {
    openTrades += bot.openTradeCount;
    const max = Number(bot.botState?.max_open_trades);
    if (Number.isFinite(max) && max > 0) {
      maxOpen += max;
    } else {
      maxKnown = false;
    }
    openAbs += sumOpenProfit(bot.openTrades).abs;
    closedAbs += bot.profit?.profit_closed_coin ?? 0;
    const t = profitToday(bot);
    if (t !== undefined) {
      today += t;
      todayKnown = true;
    }
    wins += bot.profit?.winning_trades ?? 0;
    losses += bot.profit?.losing_trades ?? 0;
    balance += bot.balance?.total_bot ?? bot.balance?.total ?? 0;
    if (!bot.isBotOnline) offline += 1;
    if (bot.botStatusAvailable) {
      if (bot.botState?.dry_run) dry += 1;
      else live += 1;
    }
  });
  const closedCount = wins + losses;
  return {
    openTrades,
    maxOpen: maxKnown && selected.value.length > 0 ? maxOpen : undefined,
    openAbs,
    closedAbs,
    today: todayKnown ? today : undefined,
    wins,
    losses,
    winRate: closedCount > 0 ? wins / closedCount : undefined,
    balance,
    live,
    dry,
    offline,
  };
});

const modeText = computed(() => {
  const { live, dry } = totals.value;
  if (live > 0 && dry > 0) return 'mixed live + dry-run';
  if (live > 0) return 'live';
  if (dry > 0) return 'dry-run';
  return '';
});

function money(value: number | undefined, signed = false): string {
  if (!sameStake.value) return 'mixed';
  if (value === undefined) return '-';
  return signed ? formatSigned(value, decimals.value) : formatPrice(value, decimals.value);
}
const mixedHint = 'The selected bots use different stake currencies - totals cannot be summed.';

const selectedWalletHistory = computed<WalletHistoryPerBot>(() => {
  const res: WalletHistoryPerBot = {};
  Object.entries(botStore.allBalanceHistory).forEach(([botId, history]) => {
    if (botStore.botStores[botId]?.isSelected) {
      res[botId] = history;
    }
  });
  return res;
});

const activityTrades = computed(() => [
  ...botStore.allOpenTradesSelectedBots,
  ...botStore.allTradesSelectedBots,
]);

const offlineSelected = computed(() =>
  botStore.selectedBots.filter((b) => !b.isBotOnline).map((b) => b.uiBotName),
);
</script>

<template>
  <div class="ft-container ft-stack">
    <template v-if="botStore.hasBots">
      <div class="ft-pagehead">
        <h1 class="ft-page-title">Overview</h1>
        <div class="ft-pagehead-actions">
          <span class="ft-hint">Scope</span>
          <FtSegmented v-model="scope" :items="scopeItems" label="Scope" />
        </div>
      </div>

      <Message v-if="offlineSelected.length" severity="warn" :closable="false">
        {{ offlineSelected.join(', ') }}
        {{ offlineSelected.length === 1 ? 'is' : 'are' }} offline - totals include the last values
        received from {{ offlineSelected.length === 1 ? 'it' : 'them' }}.
      </Message>

      <FtTiles aria-label="Key figures">
        <FtTile
          label="Open trades"
          :value="totals.openTrades"
          :sub="totals.maxOpen !== undefined ? `of ${totals.maxOpen} slots` : 'unlimited slots'"
        />
        <FtTile
          label="Open P&L"
          :value="money(totals.openAbs, true)"
          :profit="sameStake ? totals.openAbs : undefined"
          :sub="sameStake ? `${currency} unrealised` : 'mixed currencies'"
          :hint="sameStake ? 'Unrealised profit of all open trades' : mixedHint"
        />
        <FtTile
          label="P&L today"
          :value="money(totals.today, true)"
          :profit="sameStake ? totals.today : undefined"
          :sub="sameStake ? `${currency} closed today` : 'mixed currencies'"
          :hint="sameStake ? 'Profit of trades closed today' : mixedHint"
        />
        <FtTile
          label="Closed P&L"
          :value="money(totals.closedAbs, true)"
          :profit="sameStake ? totals.closedAbs : undefined"
          :sub="sameStake ? `${currency} realised, all time` : 'mixed currencies'"
          :hint="sameStake ? 'Realised profit of all closed trades' : mixedHint"
        />
        <FtTile
          label="Win rate"
          :value="totals.winRate !== undefined ? formatPercent(totals.winRate, 1) : '-'"
          :sub="`${totals.wins} W / ${totals.losses} L`"
        />
        <FtTile
          label="Balance"
          :value="sameStake ? formatPrice(totals.balance, 2) : 'mixed'"
          :sub="sameStake ? [currency, modeText].filter(Boolean).join(' · ') : 'mixed currencies'"
          :hint="sameStake ? 'Bot balance in stake currency' : mixedHint"
        />
      </FtTiles>

      <FtPanel title="Bots" flush>
        <template #actions>
          <InputText
            v-model="botFilter"
            size="small"
            placeholder="Search bots"
            aria-label="Search bots"
            class="ft-search"
          />
          <Button
            size="small"
            severity="secondary"
            label="Add bot"
            @click="loginModal?.openLoginModal()"
          >
            <template #icon><i-mdi-plus /></template>
          </Button>
          <Button
            size="small"
            severity="secondary"
            label="Manage"
            as="router-link"
            to="/settings"
            title="Rename, reorder or remove bots"
          />
        </template>
        <BotsTable :filter="botFilter" />
      </FtPanel>

      <div class="ft-grid-2">
        <FtPanel title="Balance" flush body-height="300px">
          <WalletHistoryChart :wallet-data="selectedWalletHistory" :show-title="false" />
        </FtPanel>
        <FtPanel title="Profit per day" body-height="300px">
          <PeriodBreakdown multi-bot-view />
        </FtPanel>
      </div>

      <FtPanel title="Open trades" flush>
        <template #actions>
          <span class="ft-hint">Click a trade to open it on its bot.</span>
        </template>
        <TradeList
          active-trades
          :trades="botStore.allOpenTradesSelectedBots"
          multi-bot-view
          empty-text="No open trades."
        />
      </FtPanel>

      <div class="ft-grid-2">
        <FtPanel title="Cumulative profit" flush body-height="300px">
          <CumProfitChart
            :trades="botStore.allTradesSelectedBots"
            :open-trades="botStore.allOpenTradesSelectedBots"
            :show-title="false"
          />
        </FtPanel>
        <FtPanel title="Recent activity" flush>
          <RecentActivity :trades="activityTrades" :show-bot="botStore.botCount > 1" :limit="9" />
        </FtPanel>
      </div>

      <LoginModal ref="loginModal" hide-button />
    </template>

    <FtPanel v-else>
      <FtEmpty
        title="No bot connected"
        text="Connect to a Freqtrade bot to see its trades, performance and controls. Use the Login button in the top bar."
      >
        <template #icon><i-mdi-robot-off-outline /></template>
        <template #actions>
          <RouterLink class="ft-linkbtn" to="/login">Open sign-in page</RouterLink>
          <a class="ft-linkbtn" href="https://www.freqtrade.io/en/latest/" target="_blank"
            >Freqtrade documentation</a
          >
        </template>
      </FtEmpty>
    </FtPanel>
  </div>
</template>

<style scoped>
.ft-pagehead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px 16px;
}
.ft-pagehead-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.ft-search {
  width: 180px;
}
.ft-linkbtn {
  display: inline-flex;
  align-items: center;
  height: var(--ft-h-control);
  padding: 0 11px;
  border: 1px solid var(--ft-border);
  border-radius: var(--ft-radius-control);
  background: var(--ft-panel);
  color: var(--ft-text);
  text-decoration: none;
  font-size: 12.5px;
  font-weight: 500;
}
.ft-linkbtn:hover {
  background: var(--ft-hover);
}
@media (max-width: 700px) {
  .ft-search {
    width: 130px;
  }
}
</style>
