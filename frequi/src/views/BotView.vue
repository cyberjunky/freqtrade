<script setup lang="ts">
import type { BotSection } from '@/composables/botInfo';
import type { SegmentedItem } from '@/components/ui/FtSegmented.vue';

import SectionSummary from './bot/SectionSummary.vue';
import SectionChart from './bot/SectionChart.vue';
import SectionTrades from './bot/SectionTrades.vue';
import SectionPerformance from './bot/SectionPerformance.vue';
import SectionBalance from './bot/SectionBalance.vue';
import SectionBot from './bot/SectionBot.vue';

const route = useRoute();
const botStore = useBotStore();

const botId = computed(() => String(route.params.botId ?? ''));
const bot = computed(() => botStore.botStores[botId.value]);
/** Sections only render once the wrapper store points at this page's bot. */
const ready = computed(() => !!bot.value && botStore.selectedBot === botId.value);

const section = computed<BotSection>(() => {
  const s = String(route.params.section ?? '');
  const wanted = BOT_SECTIONS.find((x) => x.value === s)?.value ?? 'summary';
  // Bots in webserver mode do not trade - only the chart and bot sections apply.
  if (bot.value?.isWebserverMode && !['chart', 'bot'].includes(wanted)) {
    return 'chart';
  }
  return wanted;
});

const sectionItems = computed<SegmentedItem<BotSection>[]>(() =>
  BOT_SECTIONS.filter((s) => !bot.value?.isWebserverMode || ['chart', 'bot'].includes(s.value)).map(
    (s) => ({
      value: s.value,
      label: s.label,
      to: { name: 'Bot', params: { botId: botId.value, section: s.value } },
    }),
  ),
);

const sectionComponents = {
  summary: SectionSummary,
  chart: SectionChart,
  trades: SectionTrades,
  performance: SectionPerformance,
  balance: SectionBalance,
  bot: SectionBot,
};

const uiState = computed(() => botUiState(bot.value));
const uiMode = computed(() => botUiMode(bot.value));
const { staleMessage } = useBotFreshness(() => bot.value);

const autoRefresh = computed({
  get: () => bot.value?.autoRefresh ?? false,
  set: (val: boolean) => bot.value?.setAutoRefresh(val),
});

const meta = computed(() => {
  const s = bot.value?.botState;
  if (!s || !bot.value?.botStatusAvailable) return [];
  return [
    s.strategy,
    [s.exchange, s.trading_mode, s.demo_trading ? '(demo)' : ''].filter(Boolean).join(' '),
    s.timeframe,
    bot.value.version ? `v${bot.value.version}` : '',
  ].filter(Boolean);
});
</script>

<template>
  <div class="ft-container ft-stack">
    <template v-if="bot && ready">
      <header class="ft-bothead" :class="{ 'is-live': uiMode === 'live' }">
        <div class="ft-bothead-id">
          <h1 class="ft-page-title">{{ bot.uiBotName }}</h1>
          <FtState :state="uiState" />
          <FtMode :mode="uiMode" />
          <span class="ft-botmeta ft-mono">
            <span v-for="m in meta" :key="m">{{ m }}</span>
          </span>
        </div>
        <div class="ft-bothead-ctl">
          <label
            class="ft-autorefresh"
            title="Automatically refresh this bot's data (open trades every 5s, the rest once a minute)"
          >
            <ToggleSwitch v-model="autoRefresh" aria-label="Auto-refresh" />
            <span>Auto-refresh</span>
          </label>
          <BotControls v-if="!bot.isWebserverMode" />
        </div>
      </header>

      <Message v-if="staleMessage" severity="warn" :closable="false" class="ft-stale">
        {{ staleMessage }}
      </Message>

      <FtSegmented :model-value="section" :items="sectionItems" label="Bot sections" />

      <FtPanel v-if="!bot.botStatusAvailable">
        <FtEmpty
          title="No data from this bot yet"
          :text="
            bot.isBotOnline
              ? 'Waiting for the first response...'
              : 'The bot is not reachable. Check that it is running and the API is enabled.'
          "
        />
      </FtPanel>
      <component :is="sectionComponents[section]" v-else :key="`${botId}-${section}`" />
    </template>
    <FtPanel v-else>
      <FtEmpty title="Bot not found" text="This bot is not configured in this browser.">
        <template #actions><RouterLink to="/">Back to overview</RouterLink></template>
      </FtEmpty>
    </FtPanel>
  </div>
</template>

<style scoped>
.ft-bothead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px 18px;
}
.ft-bothead-id {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 12px;
  min-width: 0;
}
.ft-botmeta {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 2px 12px;
  font-size: 12px;
  color: var(--ft-text-2);
}
.ft-bothead-ctl {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 14px;
}
.ft-autorefresh {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--ft-text-2);
  cursor: pointer;
  white-space: nowrap;
}
</style>
