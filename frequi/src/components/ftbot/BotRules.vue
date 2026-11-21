<script setup lang="ts">
/** Trading rules of the active bot (from show_config). */
const botStore = useBotStore();
const state = computed(() => botStore.activeBot.botState);

const roi = computed(() => {
  const r = (state.value?.minimal_roi ?? {}) as Record<string, number>;
  return Object.entries(r)
    .sort((a, b) => Number(a[0]) - Number(b[0]))
    .map(([minutes, ratio]) => `${minutes}m: ${formatPercent(ratio, 2)}`);
});

const orderTypes = computed(() => {
  const o = state.value?.order_types;
  if (!o) return [];
  return [
    ['entry', o.entry ?? o.buy],
    ['exit', o.exit ?? o.sell],
    ['stoploss', o.stoploss],
    ['force entry', o.force_entry ?? o.forcebuy],
    ['force exit', o.force_exit ?? o.forcesell],
    ['emergency exit', o.emergency_exit ?? o.emergencysell],
  ].filter(([, v]) => !!v) as [string, string][];
});

const entryPricing = computed(() => state.value?.entry_pricing ?? state.value?.bid_strategy);
const exitPricing = computed(() => state.value?.exit_pricing ?? state.value?.ask_strategy);
const timeout = computed(() => state.value?.unfilledtimeout);
const yesNo = (v: boolean | undefined) => (v ? 'yes' : 'no');
</script>

<template>
  <dl v-if="state" class="ft-kv">
    <dt>Stake per trade</dt>
    <dd>{{ state.stake_amount }} {{ state.stake_currency }}</dd>
    <dt>Max open trades</dt>
    <dd>{{ Number(state.max_open_trades) > 0 ? state.max_open_trades : 'unlimited' }}</dd>
    <dt>Stoploss</dt>
    <dd>
      <span class="ft-neg">{{ formatSignedPercent(state.stoploss, 2) }}</span>
      <span v-if="'stoploss_on_exchange' in state" class="ft-dim">
        · on exchange: {{ yesNo(state.stoploss_on_exchange) }}</span
      >
    </dd>
    <dt>Trailing stop</dt>
    <dd>
      <template v-if="state.trailing_stop">
        {{ formatSignedPercent(state.trailing_stop_positive, 2) }}
        <span class="ft-dim"
          >· offset {{ formatPercent(state.trailing_stop_positive_offset, 2) }} · only after offset:
          {{ yesNo(state.trailing_only_offset_is_reached) }}</span
        >
      </template>
      <template v-else>off</template>
    </dd>
    <dt>Minimal ROI</dt>
    <dd>
      <template v-if="roi.length">
        <span v-for="r in roi" :key="r" class="ft-rule-item">{{ r }}</span>
      </template>
      <template v-else>N/A</template>
    </dd>
    <dt>Order types</dt>
    <dd>
      <span v-for="[k, val] in orderTypes" :key="k" class="ft-rule-item"
        ><span class="ft-dim">{{ k }}</span> {{ val }}</span
      >
    </dd>
    <template v-if="entryPricing">
      <dt>Entry pricing</dt>
      <dd>
        {{ entryPricing.price_side }}
        <span class="ft-dim"
          >· order book: {{ yesNo(entryPricing.use_order_book) }}
          {{ entryPricing.use_order_book ? `(top ${entryPricing.order_book_top})` : '' }}</span
        >
      </dd>
    </template>
    <template v-if="exitPricing">
      <dt>Exit pricing</dt>
      <dd>
        {{ exitPricing.price_side }}
        <span class="ft-dim"
          >· order book: {{ yesNo(exitPricing.use_order_book) }}
          {{ exitPricing.use_order_book ? `(top ${exitPricing.order_book_top})` : '' }}</span
        >
      </dd>
    </template>
    <template v-if="timeout">
      <dt>Unfilled timeout</dt>
      <dd>
        entry {{ timeout.entry ?? timeout.buy ?? '-' }} / exit
        {{ timeout.exit ?? timeout.sell ?? '-' }} {{ timeout.unit }}
      </dd>
    </template>
    <dt>Position adjustment</dt>
    <dd>
      {{ yesNo(state.position_adjustment_enable) }}
      <span
        v-if="state.position_adjustment_enable && state.max_entry_position_adjustment !== undefined"
        class="ft-dim"
        >· max {{ state.max_entry_position_adjustment }} extra entries</span
      >
    </dd>
    <dt>Short allowed</dt>
    <dd>{{ yesNo(state.short_allowed) }}</dd>
    <dt>Force entry</dt>
    <dd>{{ state.force_entry_enable ? 'enabled' : 'disabled' }}</dd>
  </dl>
</template>

<style scoped>
.ft-rule-item {
  display: inline-block;
  margin-left: 12px;
  white-space: nowrap;
}
</style>
