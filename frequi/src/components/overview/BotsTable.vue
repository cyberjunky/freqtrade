<script setup lang="ts">
import type { BotUiMode, BotUiState } from '@/composables/botInfo';

interface BotRow {
  botId: string;
  name: string;
  state: BotUiState;
  mode: BotUiMode;
  strategy: string;
  exchange: string;
  market: string;
  openTrades: number;
  maxOpenTrades: number | undefined;
  profitToday: number | undefined;
  profitOpen: number;
  profitOpenRatio: number | undefined;
  profitClosed: number | undefined;
  profitClosedRatio: number | undefined;
  balance: number | undefined;
  currency: string;
  decimals: number;
  selected: boolean;
  stale: string | undefined;
}

type SortKey =
  | 'name'
  | 'state'
  | 'mode'
  | 'strategy'
  | 'exchange'
  | 'openTrades'
  | 'profitToday'
  | 'profitOpen'
  | 'profitClosed'
  | 'balance';

const props = defineProps<{ filter: string }>();

const botStore = useBotStore();
const router = useRouter();
const now = useTimestamp({ interval: 5000 });

const rows = computed<BotRow[]>(() =>
  botStore.availableBotsSorted.map((desc) => {
    const bot = botStore.botStores[desc.botId];
    const state = botUiState(bot);
    const open = sumOpenProfit(bot?.openTrades);
    const online = state !== 'offline';
    const maxOpen = Number(bot?.botState?.max_open_trades);
    let stale: string | undefined;
    if (bot && !online) {
      stale = bot.lastUpdate
        ? `Offline - values are ${formatAge(now.value - bot.lastUpdate)} old`
        : 'Offline - no data received';
    }
    return {
      botId: desc.botId,
      name: bot?.uiBotName || desc.botName || desc.botId,
      state,
      mode: botUiMode(bot),
      strategy: bot?.botState?.strategy ?? '',
      exchange: bot?.botState?.exchange ?? '',
      market: bot?.botState?.trading_mode ?? '',
      openTrades: bot?.openTradeCount ?? 0,
      maxOpenTrades: Number.isFinite(maxOpen) && maxOpen > 0 ? maxOpen : undefined,
      profitToday: bot?.isTrading ? profitToday(bot) : undefined,
      profitOpen: open.abs,
      profitOpenRatio: open.ratio,
      profitClosed: bot?.profit?.profit_closed_coin,
      profitClosedRatio: bot?.profit?.profit_closed_ratio,
      balance: bot?.balance?.total_bot ?? bot?.balance?.total,
      currency: bot?.stakeCurrency ?? '',
      decimals: bot?.stakeCurrencyDecimals ?? 3,
      selected: bot?.isSelected ?? false,
      stale,
    };
  }),
);

const sortKey = ref<SortKey | ''>('');
const sortDir = ref<1 | -1>(1);

function sortBy(key: SortKey) {
  if (sortKey.value === key) {
    if (sortDir.value === 1) {
      sortDir.value = -1;
    } else {
      // third click: back to the configured bot order
      sortKey.value = '';
      sortDir.value = 1;
    }
  } else {
    sortKey.value = key;
    sortDir.value = 1;
  }
}

const visibleRows = computed<BotRow[]>(() => {
  const needle = props.filter.trim().toLowerCase();
  let res = rows.value;
  if (needle) {
    res = res.filter((r) =>
      [r.name, r.strategy, r.exchange, r.state, r.mode === 'dry' ? 'dry-run' : r.mode]
        .join(' ')
        .toLowerCase()
        .includes(needle),
    );
  }
  const key = sortKey.value;
  if (key) {
    res = res.slice().sort((a, b) => {
      const va = a[key];
      const vb = b[key];
      if (va === vb) return 0;
      if (va === undefined) return 1;
      if (vb === undefined) return -1;
      return (va > vb ? 1 : -1) * sortDir.value;
    });
  }
  return res;
});

function ariaSort(key: SortKey) {
  if (sortKey.value !== key) return 'none';
  return sortDir.value === 1 ? 'ascending' : 'descending';
}

function openBot(botId: string) {
  router.push({ name: 'Bot', params: { botId } });
}

function toggleSelected(botId: string, value: boolean) {
  const bot = botStore.botStores[botId];
  if (bot) {
    bot.isSelected = value;
  }
}

const columns: { key: SortKey; label: string; num?: boolean }[] = [
  { key: 'name', label: 'Bot' },
  { key: 'state', label: 'State' },
  { key: 'mode', label: 'Mode' },
  { key: 'strategy', label: 'Strategy' },
  { key: 'exchange', label: 'Exchange' },
  { key: 'openTrades', label: 'Open', num: true },
  { key: 'profitToday', label: 'P&L today', num: true },
  { key: 'profitOpen', label: 'P&L open', num: true },
  { key: 'profitClosed', label: 'P&L closed', num: true },
  { key: 'balance', label: 'Balance', num: true },
];
</script>

<template>
  <div class="ft-scroll-x">
    <table class="ft-table ft-bots">
      <thead>
        <tr>
          <th v-if="botStore.botCount > 1" class="ft-col-check" title="Include in the totals above">
            <span class="sr-only">Include in totals</span>
          </th>
          <th
            v-for="col in columns"
            :key="col.key"
            :class="{ 'ft-num': col.num }"
            :aria-sort="ariaSort(col.key)"
          >
            <button type="button" class="ft-sort" @click="sortBy(col.key)">
              {{ col.label }}
              <span class="ft-sort-ind" aria-hidden="true">{{
                sortKey === col.key ? (sortDir === 1 ? '▲' : '▼') : ''
              }}</span>
            </button>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in visibleRows"
          :key="row.botId"
          class="ft-bot-row"
          :class="{ 'is-offline': row.state === 'offline' }"
          @click="openBot(row.botId)"
        >
          <td v-if="botStore.botCount > 1" class="ft-col-check" @click.stop>
            <Checkbox
              :model-value="row.selected"
              binary
              :aria-label="`Include ${row.name} in totals`"
              title="Include in the totals above"
              @update:model-value="toggleSelected(row.botId, $event)"
            />
          </td>
          <td>
            <RouterLink
              class="ft-bot-name"
              :to="{ name: 'Bot', params: { botId: row.botId } }"
              @click.stop
              >{{ row.name }}</RouterLink
            >
            <div v-if="row.stale" class="ft-bot-stale">{{ row.stale }}</div>
          </td>
          <td><FtState :state="row.state" /></td>
          <td><FtMode :mode="row.mode" /></td>
          <td>{{ row.strategy || '-' }}</td>
          <td>
            {{ row.exchange || '-' }}
            <span v-if="row.market" class="ft-dim">{{ row.market }}</span>
          </td>
          <td class="ft-num">
            {{ row.openTrades }}<span class="ft-dim"> / {{ row.maxOpenTrades ?? '\u221e' }}</span>
          </td>
          <td class="ft-num">
            <FtProfit
              v-if="row.profitToday !== undefined"
              :abs="row.profitToday"
              :decimals="row.decimals"
            />
            <span v-else class="ft-dim">-</span>
          </td>
          <td class="ft-num">
            <FtProfit
              v-if="row.openTrades > 0"
              :abs="row.profitOpen"
              :ratio="row.profitOpenRatio"
              :decimals="row.decimals"
            />
            <span v-else class="ft-dim">-</span>
          </td>
          <td class="ft-num">
            <FtProfit
              v-if="row.profitClosed !== undefined"
              :abs="row.profitClosed"
              :ratio="row.profitClosedRatio"
              :decimals="row.decimals"
            />
            <span v-else class="ft-dim">-</span>
          </td>
          <td class="ft-num">
            <template v-if="row.balance !== undefined">
              {{ formatPrice(row.balance, 2) }}
              <span class="ft-dim">{{ row.currency }}</span>
            </template>
            <span v-else class="ft-dim">-</span>
          </td>
        </tr>
        <tr v-if="visibleRows.length === 0">
          <td :colspan="columns.length + 1" class="ft-none">No bot matches "{{ filter }}".</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.ft-bots {
  min-width: 980px;
}
.ft-bot-row {
  cursor: pointer;
}
.ft-bot-row.is-offline td:not(:nth-child(-n + 3)) {
  opacity: 0.55;
}
.ft-bot-name {
  white-space: nowrap;
  font-weight: 600;
  color: var(--ft-text);
  text-decoration: none;
}
.ft-bot-name:hover {
  color: var(--ft-primary);
  text-decoration: underline;
}
.ft-bot-stale {
  font-size: 11px;
  color: var(--ft-warning);
}
.ft-col-check {
  width: 34px;
  padding-right: 0 !important;
}
.ft-sort {
  all: unset;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font: inherit;
  letter-spacing: inherit;
  text-transform: inherit;
  color: inherit;
}
.ft-sort:hover {
  color: var(--ft-text);
}
.ft-sort:focus-visible {
  outline: 2px solid var(--ft-primary);
  outline-offset: 3px;
}
.ft-sort-ind {
  font-size: 8px;
  min-width: 8px;
  color: var(--ft-primary);
}
.ft-none {
  text-align: center;
  color: var(--ft-muted);
  padding: 22px 10px !important;
}
</style>
