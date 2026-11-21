<script setup lang="ts">
import type { Trade } from '@/types';

/** Recent entries / exits derived from the trades the bots already loaded. */
const props = withDefaults(
  defineProps<{
    trades: Trade[];
    limit?: number;
    showBot?: boolean;
  }>(),
  { limit: 12, showBot: false },
);

interface ActivityItem {
  key: string;
  ts: number;
  kind: 'entry' | 'exit';
  trade: Trade;
}

const items = computed<ActivityItem[]>(() => {
  const res: ActivityItem[] = [];
  props.trades.forEach((trade) => {
    if (trade.open_timestamp) {
      res.push({
        key: `${trade.botTradeId}-o`,
        ts: trade.open_timestamp,
        kind: 'entry',
        trade,
      });
    }
    if (!trade.is_open && trade.close_timestamp) {
      res.push({
        key: `${trade.botTradeId}-c`,
        ts: trade.close_timestamp,
        kind: 'exit',
        trade,
      });
    }
  });
  return res.sort((a, b) => b.ts - a.ts).slice(0, props.limit);
});
</script>

<template>
  <ul v-if="items.length" class="ft-activity">
    <li v-for="item in items" :key="item.key" class="ft-activity-row">
      <span class="ft-activity-time ft-mono"><DateTimeTZ :date="item.ts" /></span>
      <FtBadge :kind="item.kind === 'entry' ? 'default' : 'neutral'">{{
        item.kind === 'entry' ? 'ENTRY' : 'EXIT'
      }}</FtBadge>
      <span class="ft-activity-main">
        <RouterLink
          class="ft-activity-pair ft-mono"
          :to="{ name: 'Bot', params: { botId: item.trade.botId, section: 'trades' } }"
          >{{ item.trade.pair }}</RouterLink
        >
        <FtSide v-if="item.trade.is_short !== undefined" :short="item.trade.is_short" />
        <span v-if="showBot" class="ft-dim">{{ item.trade.botName }}</span>
        <span v-if="item.kind === 'exit' && item.trade.exit_reason" class="ft-dim">{{
          item.trade.exit_reason
        }}</span>
        <span v-else-if="item.kind === 'entry' && item.trade.enter_tag" class="ft-dim">{{
          item.trade.enter_tag
        }}</span>
      </span>
      <span class="ft-activity-val ft-num">
        <FtProfit
          v-if="item.kind === 'exit'"
          :abs="item.trade.profit_abs"
          :ratio="item.trade.profit_ratio"
        />
        <template v-else>@ {{ formatPrice(item.trade.open_rate) }}</template>
      </span>
    </li>
  </ul>
  <FtEmpty v-else title="No activity yet" text="Entries and exits will show up here." />
</template>

<style scoped>
.ft-activity {
  list-style: none;
  margin: 0;
  padding: 0;
  font-size: 12.5px;
}
.ft-activity-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 18px;
  border-bottom: 1px solid var(--ft-border);
  min-width: 0;
}
.ft-activity-row:last-child {
  border-bottom: 0;
}
.ft-activity-time {
  color: var(--ft-muted);
  font-size: 11.5px;
  flex: 0 0 auto;
}
.ft-activity-main {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1 1 auto;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.ft-activity-pair {
  color: var(--ft-text);
  font-weight: 500;
  text-decoration: none;
}
.ft-activity-pair:hover {
  text-decoration: underline;
}
.ft-activity-val {
  flex: 0 0 auto;
  color: var(--ft-text-2);
}
@media (max-width: 700px) {
  .ft-activity-row {
    flex-wrap: wrap;
    padding: 8px 12px;
    gap: 4px 8px;
  }
  .ft-activity-main {
    flex: 1 1 60%;
  }
}
</style>
