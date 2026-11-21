<script setup lang="ts">
import type { Lock, Trade } from '@/types';

interface CombinedPairList {
  pair: string;
  lockReason: string;
  profitString: string;
  trade?: Trade;
  locks?: Lock;
  profit: number;
  profitAbs: number;
  tradeCount: number;
}

const props = withDefaults(
  defineProps<{
    pairlist: string[];
    currentLocks?: Lock[];
    trades: Trade[];
    sortMethod?: string;
    backtestMode?: boolean;
    startingBalance?: number;
  }>(),
  {
    currentLocks: () => [],
    sortMethod: 'normal',
    backtestMode: false,
    startingBalance: 0,
  },
);
const botStore = useBotStore();

const filterText = ref('');
const combinedPairList = computed(() => {
  const comb: CombinedPairList[] = [];

  props.pairlist.forEach((pair) => {
    const trades: Trade[] = props.trades.filter((el) => el.pair === pair);
    const allLocks = props.currentLocks.filter((el) => el.pair === pair);
    let lockReason = '';
    let locks;

    // Sort to have longer timeframe in front
    allLocks.sort((a, b) => (a.lock_end_timestamp > b.lock_end_timestamp ? -1 : 1));
    if (allLocks.length > 0) {
      [locks] = allLocks;
      lockReason = `${timestampms(locks.lock_end_timestamp)} - ${locks.side} - ${locks.reason}`;
    }
    let profitString = '';
    let profit = 0;
    let profitAbs = 0;
    trades.forEach((trade) => {
      profit += trade.profit_ratio ?? 0;
      profitAbs += trade.profit_abs ?? 0;
    });
    if (props.sortMethod == 'profit' && props.startingBalance) {
      profit = profitAbs / props.startingBalance;
    }
    const tradeCount = trades.length;
    const trade = tradeCount ? trades[0] : undefined;
    if (trades.length > 0) {
      profitString = `Current profit: ${formatPercent(profit)}`;
    }
    if (trade) {
      profitString += `\nOpen since: ${timestampms(trade.open_timestamp)}`;
    }
    if (
      filterText.value === '' ||
      pair.toLocaleLowerCase().includes(filterText.value.toLocaleLowerCase())
    ) {
      comb.push({ pair, trade, locks, lockReason, profitString, profit, profitAbs, tradeCount });
    }
  });

  if (props.sortMethod === 'profit') {
    comb.sort((a, b) => {
      if (a.profit > b.profit) {
        return -1;
      }
      return 1;
    });
  } else {
    // sort Pairs: "with open trade" -> available -> locked
    comb.sort((a, b) => {
      if (a.trade && !b.trade) {
        return -1;
      }
      if (a.trade && b.trade) {
        // 2 open trade pairs
        return a.trade.trade_id > b.trade.trade_id ? 1 : -1;
      }
      if (!a.locks && b.locks) {
        return -1;
      }
      if (a.locks && b.locks) {
        // Both have locks
        return a.locks.lock_end_timestamp > b.locks.lock_end_timestamp ? 1 : -1;
      }
      return 1;
    });
  }
  return comb;
});
</script>

<template>
  <div class="ft-pairs">
    <InputText
      id="trade-filter"
      v-model="filterText"
      type="text"
      size="small"
      placeholder="Filter pairs"
      aria-label="Filter pairs"
      class="ft-pairs-filter"
    />
    <ul class="ft-pairs-list">
      <li
        v-for="comb in combinedPairList"
        :key="comb.pair"
        :aria-label="comb.pair"
        class="ft-pair-row"
        :class="{ 'is-selected': comb.pair === botStore.activeBot.selectedPair }"
        :title="`${formatPriceCurrency(comb.profitAbs, botStore.activeBot.stakeCurrency, botStore.activeBot.stakeCurrencyDecimals)} - ${comb.pair} - ${comb.tradeCount} trades`"
      >
        <button
          type="button"
          class="ft-pair-btn"
          :aria-pressed="comb.pair === botStore.activeBot.selectedPair"
          @click="botStore.activeBot.selectedPair = comb.pair"
        >
          <span class="ft-pair-name ft-mono">
            {{ comb.pair }}
            <span v-if="comb.locks" :title="comb.lockReason" class="ft-pair-lock">
              <i-mdi-lock aria-label="locked" />
            </span>
          </span>
          <TradeProfit v-if="comb.trade && !backtestMode" :trade="comb.trade" />
          <ProfitPill
            v-if="backtestMode && comb.tradeCount > 0"
            :profit-ratio="comb.profit"
            :stake-currency="botStore.activeBot.stakeCurrency"
          />
        </button>
      </li>
      <li v-if="combinedPairList.length === 0" class="ft-pairs-empty">No pairs.</li>
    </ul>
  </div>
</template>

<style scoped>
.ft-pairs {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
  text-align: left;
}
.ft-pairs-filter {
  width: 100%;
}
.ft-pairs-list {
  list-style: none;
  margin: 0;
  padding: 0;
  border: 1px solid var(--ft-border);
  border-radius: var(--ft-radius-control);
  overflow: hidden;
}
.ft-pair-row {
  border-bottom: 1px solid var(--ft-border);
}
.ft-pair-row:last-child {
  border-bottom: 0;
}
.ft-pair-btn {
  all: unset;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  padding: 5px 9px;
  font-size: 12px;
  cursor: pointer;
}
.ft-pair-btn:hover {
  background: var(--ft-hover);
}
.ft-pair-btn:focus-visible {
  outline: 2px solid var(--ft-primary);
  outline-offset: -2px;
}
.ft-pair-row.is-selected .ft-pair-btn {
  background: var(--ft-selected);
  box-shadow: inset 2px 0 0 var(--ft-primary);
}
.ft-pair-name {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.ft-pair-lock {
  color: var(--ft-warning);
  display: inline-flex;
}
.ft-pairs-empty {
  padding: 12px;
  color: var(--ft-muted);
  text-align: center;
}
</style>
