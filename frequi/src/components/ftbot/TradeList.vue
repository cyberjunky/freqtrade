<script setup lang="ts">
import type { MultiDeletePayload, MultiForceExitPayload, Trade } from '@/types';

import { useRouter } from 'vue-router';

enum ModalReasons {
  removeTrade,
  forceExit,
  forceExitPartial,
  cancelOpenOrder,
}

const props = withDefaults(
  defineProps<{
    trades: Trade[];
    title?: string;
    stakeCurrency?: string;
    activeTrades?: boolean;
    showFilter?: boolean;
    multiBotView?: boolean;
    emptyText?: string;
    /** Rows per page for non-active trade lists */
    rows?: number;
  }>(),
  {
    title: 'Trades',
    stakeCurrency: '',
    activeTrades: false,
    showFilter: false,
    multiBotView: false,
    emptyText: 'No Trades to show.',
    rows: 15,
  },
);

const botStore = useBotStore();
const router = useRouter();
const settingsStore = useSettingsStore();
const selectedItem = ref();
const filterText = ref('');
const feTrade = ref<Trade>({} as Trade);
const perPage = computed(() => (props.activeTrades ? 200 : props.rows));
const forceExitVisible = ref(false);
const removeTradeVisible = ref(false);
const confirmExitText = ref('');
const confirmExitTitle = ref('');
const confirmExitLabel = ref('Confirm');
const confirmExitValue = ref<ModalReasons | null>(null);

const increasePosition = ref({ visible: false, trade: {} as Trade });

function botOf(trade: Trade) {
  return botStore.botStores[trade.botId] ?? botStore.activeBot;
}
function formatStake(trade: Trade, value: number) {
  return formatPrice(value, botOf(trade)?.stakeCurrencyDecimals ?? 3);
}
function isLive(trade: Trade) {
  return botUiMode(botOf(trade)) === 'live';
}

interface TradeColumn {
  field: string;
  header: string;
  num?: boolean;
}

const tableFields = computed<TradeColumn[]>(() => {
  const fields: TradeColumn[] = [
    { field: 'trade_id', header: 'ID', num: true },
    { field: 'pair', header: 'Pair' },
    { field: 'amount', header: 'Amount', num: true },
    props.activeTrades
      ? { field: 'stake_amount', header: 'Stake', num: true }
      : { field: 'max_stake_amount', header: 'Total stake', num: true },
    { field: 'open_rate', header: 'Open rate', num: true },
    {
      field: props.activeTrades ? 'current_rate' : 'close_rate',
      header: props.activeTrades ? 'Current rate' : 'Close rate',
      num: true,
    },
    { field: 'profit', header: props.activeTrades ? 'Current profit' : 'Profit', num: true },
    { field: 'open_timestamp', header: 'Opened', num: true },
    ...(props.activeTrades
      ? [{ field: 'actions', header: 'Actions' }]
      : [
          { field: 'close_timestamp', header: 'Closed', num: true },
          { field: 'exit_reason', header: 'Close reason' },
        ]),
  ];
  if (props.multiBotView) {
    fields.unshift({ field: 'botName', header: 'Bot' });
  }
  return fields;
});

const filteredTrades = computed(() => {
  const needle = filterText.value.toLowerCase();
  if (!needle) return props.trades;
  return props.trades.filter(
    (t) =>
      t.pair.toLowerCase().includes(needle) ||
      t.exit_reason?.toLowerCase().includes(needle) ||
      t.enter_tag?.toLowerCase().includes(needle) ||
      String(t.trade_id) === needle ||
      (props.multiBotView ? t.botName?.toLowerCase().includes(needle) : false),
  );
});

const feOrderType = ref<string | undefined>(undefined);
function forceExitHandler(item: Trade, ordertype: string | undefined = undefined) {
  feTrade.value = item;
  confirmExitValue.value = ModalReasons.forceExit;
  confirmExitTitle.value = 'Force exit trade';
  confirmExitLabel.value = 'Force exit';
  confirmExitText.value = `Really exit trade ${item.trade_id} (Pair ${item.pair}) using ${ordertype ?? 'the configured'} order?`;
  feOrderType.value = ordertype;
  if (settingsStore.confirmDialog === true) {
    removeTradeVisible.value = true;
  } else {
    forceExitExecuter();
  }
}

function forceExitExecuter() {
  if (confirmExitValue.value === ModalReasons.removeTrade) {
    const payload: MultiDeletePayload = {
      tradeid: String(feTrade.value.trade_id),
      botId: feTrade.value.botId,
    };
    botStore.deleteTradeMulti(payload).catch((error) => console.log(error.response));
  }
  if (confirmExitValue.value === ModalReasons.forceExit) {
    const payload: MultiForceExitPayload = {
      tradeid: String(feTrade.value.trade_id),
      botId: feTrade.value.botId,
    };
    if (feOrderType.value) {
      payload.ordertype = feOrderType.value;
    }
    botStore
      .forceSellMulti(payload)
      .then((xxx) => console.log(xxx))
      .catch((error) => console.log(error.response));
  }
  if (confirmExitValue.value === ModalReasons.cancelOpenOrder) {
    const payload: MultiDeletePayload = {
      tradeid: String(feTrade.value.trade_id),
      botId: feTrade.value.botId,
    };
    botStore.cancelOpenOrderMulti(payload);
  }

  feOrderType.value = undefined;
  removeTradeVisible.value = false;
}

function removeTradeHandler(item: Trade) {
  confirmExitTitle.value = 'Delete trade';
  confirmExitLabel.value = 'Delete trade';
  confirmExitText.value = `Really delete trade ${item.trade_id} (Pair ${item.pair})? This removes it from the bot's database - open orders are cancelled, the position on the exchange is NOT closed.`;
  confirmExitValue.value = ModalReasons.removeTrade;
  feTrade.value = item;
  removeTradeVisible.value = true;
}

function forceExitPartialHandler(item: Trade) {
  feTrade.value = item;
  forceExitVisible.value = true;
}

function cancelOpenOrderHandler(item: Trade) {
  confirmExitTitle.value = 'Cancel open order';
  confirmExitLabel.value = 'Cancel order';
  confirmExitText.value = `Cancel open order for trade ${item.trade_id} (Pair ${item.pair})?`;
  feTrade.value = item;
  confirmExitValue.value = ModalReasons.cancelOpenOrder;
  removeTradeVisible.value = true;
}

function reloadTradeHandler(item: Trade) {
  botStore.reloadTradeMulti({ tradeid: String(item.trade_id), botId: item.botId });
}

function handleForceEntry(item: Trade) {
  increasePosition.value.trade = item;
  increasePosition.value.visible = true;
}

const onRowClicked = ({ data: item }: { data: Trade }) => {
  if (props.multiBotView) {
    // Overview: open the trade on its bot
    if (botStore.selectedBot !== item.botId) {
      botStore.selectBot(item.botId);
    }
    botStore.botStores[item.botId]?.setDetailTrade(item);
    router.push({
      name: 'Bot',
      params: { botId: item.botId, section: item.is_open ? 'summary' : 'trades' },
    });
    return;
  }
  if (item && item.trade_id !== botStore.activeBot.detailTradeId) {
    botStore.activeBot.setDetailTrade(item);
  } else {
    botStore.activeBot.setDetailTrade(null);
  }
};

watch(
  () => botStore.activeBotorUndefined?.detailTradeId,
  (val) => {
    const index = props.trades.findIndex((v) => v.trade_id === val);
    // Unselect when another tradeTable is selected!
    if (index < 0) {
      selectedItem.value = undefined;
    }
  },
);
</script>

<template>
  <div class="ft-tradelist">
    <div v-if="showFilter" class="ft-tl-toolbar">
      <InputText
        v-model="filterText"
        placeholder="Search pair, tag, close reason"
        aria-label="Search trades"
        class="ft-tl-search"
        size="small"
      />
      <span class="ft-hint ft-mono">{{ filteredTrades.length }} / {{ trades.length }}</span>
    </div>
    <DataTable
      v-model:selection="selectedItem"
      :value="filteredTrades"
      :rows="perPage"
      :paginator="!activeTrades && filteredTrades.length > perPage"
      selection-mode="single"
      size="small"
      scrollable
      class="ft-nowrap"
      @row-click="onRowClicked"
    >
      <template #empty>
        {{ filterText ? `No trade matches "${filterText}".` : emptyText }}
      </template>
      <Column
        v-for="column in tableFields"
        :key="column.field"
        :field="column.field"
        :header="column.header"
        :class="{ 'ft-num': column.num }"
      >
        <template #body="{ data, field, index }">
          <template v-if="field === 'trade_id'">
            {{ data.trade_id }}
          </template>
          <template v-else-if="field === 'pair'">
            <span class="ft-tl-pair">
              <span class="ft-mono">{{ data.pair }}</span>
              <FtSide
                v-if="data.trading_mode && data.trading_mode !== 'spot'"
                :short="!!data.is_short"
              />
              <FtBadge
                v-if="data.open_order_id || data.has_open_orders"
                kind="warn"
                title="This trade has open orders"
                >ORDER</FtBadge
              >
              <FtBadge v-if="multiBotView && isLive(data as Trade)" kind="warn">LIVE</FtBadge>
            </span>
          </template>
          <template v-else-if="field === 'actions'">
            <TradeActionsPopover
              :id="index"
              :enable-force-entry="botOf(data as Trade)?.botState.force_entry_enable"
              :trade="data as Trade"
              :bot-features="botOf(data as Trade).botFeatures"
              @delete-trade="removeTradeHandler(data as Trade)"
              @force-exit="forceExitHandler"
              @force-exit-partial="forceExitPartialHandler"
              @cancel-open-order="cancelOpenOrderHandler"
              @reload-trade="reloadTradeHandler"
              @force-entry="handleForceEntry"
            />
          </template>
          <template v-else-if="field === 'stake_amount' || field === 'max_stake_amount'">
            {{ formatStake(data as Trade, data[field] ?? data.stake_amount) }}
            <span v-if="data.trading_mode && data.trading_mode !== 'spot'" class="ft-dim"
              >{{ data.leverage }}x</span
            >
          </template>
          <template
            v-else-if="field === 'open_rate' || field === 'current_rate' || field === 'close_rate'"
          >
            {{ formatPrice(data[field]) }}
          </template>
          <template v-else-if="field === 'amount'">
            {{ formatPrice(data[field]) }}
          </template>
          <template v-else-if="field === 'profit'">
            <TradeProfit :trade="data" />
          </template>
          <template v-else-if="field === 'open_timestamp'">
            <DateTimeTZ :date="data.open_timestamp" />
          </template>
          <template v-else-if="field === 'close_timestamp'">
            <DateTimeTZ :date="data.close_timestamp ?? 0" />
          </template>
          <template v-else>
            {{ data[field as string] }}
          </template>
        </template>
      </Column>
    </DataTable>

    <ForceExitForm
      v-if="activeTrades"
      v-model="forceExitVisible"
      :trade="feTrade"
      :stake-currency-decimals="botOf(feTrade)?.botState?.stake_currency_decimals ?? 3"
    />
    <ForceEntryForm
      v-model="increasePosition.visible"
      :pair="increasePosition.trade?.pair"
      position-increase
    />

    <Dialog
      v-model:visible="removeTradeVisible"
      :modal="true"
      :header="confirmExitTitle"
      :draggable="false"
      :style="{ width: '440px' }"
    >
      <p>{{ confirmExitText }}</p>
      <p v-if="feTrade.botId && isLive(feTrade)" class="ft-tl-warn">
        <i-mdi-alert aria-hidden="true" /> LIVE bot - this affects real money.
      </p>
      <template #footer>
        <Button label="Cancel" severity="secondary" autofocus @click="removeTradeVisible = false" />
        <Button
          :label="confirmExitLabel"
          severity="danger"
          class="ft-danger-solid"
          @click="forceExitExecuter"
        />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.ft-tradelist {
  min-width: 0;
  width: 100%;
}
.ft-tl-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--ft-border);
}
.ft-tl-search {
  width: 260px;
  max-width: 70%;
}
.ft-tl-pair {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.ft-tl-warn {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 10px 0 0;
  color: var(--ft-warning);
  font-weight: 600;
  font-size: 12px;
}
.ft-nowrap :deep(td),
.ft-nowrap :deep(th) {
  white-space: nowrap;
}
.ft-nowrap :deep(tbody > tr) {
  cursor: pointer;
}
</style>
