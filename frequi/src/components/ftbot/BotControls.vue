<script setup lang="ts">
import type { MsgBoxObject } from '@/components/general/MessageBox.vue';
import type MessageBox from '@/components/general/MessageBox.vue';

import type { ForceExitPayload } from '@/types';

import ForceEntryForm from './ForceEntryForm.vue';

const botStore = useBotStore();
const forceEnter = ref<boolean>(false);
const msgBox = ref<InstanceType<typeof MessageBox>>();

const bot = computed(() => botStore.activeBot);
const uiState = computed(() => botUiState(bot.value));
const isRunning = computed(() => uiState.value === 'running' || uiState.value === 'paused');
const isLive = computed(() => botUiMode(bot.value) === 'live');
const liveWarning = computed(() =>
  isLive.value ? 'LIVE bot - this affects real money.' : undefined,
);
const disabled = computed(() => !bot.value.isTrading || !bot.value.isBotOnline);

const handleStopBot = () => {
  const msg: MsgBoxObject = {
    title: `Stop ${bot.value.uiBotName}?`,
    message:
      'The bot loop stops. Open trades are no longer managed (no exits, no stoploss updates) until you start it again.',
    confirmLabel: 'Stop bot',
    danger: true,
    warning: liveWarning.value,
    accept: () => {
      bot.value.stopBot();
    },
  };
  msgBox.value?.show(msg);
};

const handleStopBuy = () => {
  const msg: MsgBoxObject = {
    title: `Pause entries on ${bot.value.uiBotName}?`,
    message:
      'Freqtrade will continue to handle open trades, but will not enter new trades or increase position sizes.',
    confirmLabel: 'Pause entries',
    warning: liveWarning.value,
    accept: () => {
      bot.value.stopBuy();
    },
  };
  msgBox.value?.show(msg);
};

const handleReloadConfig = () => {
  const msg: MsgBoxObject = {
    title: `Reload config of ${bot.value.uiBotName}?`,
    message:
      'Reloads the configuration including the strategy and resets all settings changed on the fly.',
    confirmLabel: 'Reload config',
    warning: liveWarning.value,
    accept: () => {
      bot.value.reloadConfig();
    },
  };
  msgBox.value?.show(msg);
};

const handleForceExit = () => {
  const count = bot.value.openTradeCount;
  const msg: MsgBoxObject = {
    title: 'Force exit ALL trades?',
    message: `This creates exit orders for all ${count} open trade${count === 1 ? '' : 's'} of ${bot.value.uiBotName}.`,
    confirmLabel: 'Force exit all',
    danger: true,
    warning: liveWarning.value,
    accept: () => {
      const payload: ForceExitPayload = {
        tradeid: 'all',
      };
      bot.value.forceexit(payload);
    },
  };
  msgBox.value?.show(msg);
};
</script>

<template>
  <div class="ft-controls" role="group" aria-label="Bot controls">
    <Button
      severity="secondary"
      label="Start"
      :disabled="disabled || uiState === 'running'"
      title="Start trading"
      @click="bot.startBot()"
    >
      <template #icon><i-mdi-play /></template>
    </Button>
    <Button
      severity="secondary"
      label="Pause entries"
      :disabled="disabled || uiState !== 'running'"
      title="Pause (StopBuy) - open trades are still handled, but no new trades are entered."
      @click="handleStopBuy()"
    >
      <template #icon><i-mdi-pause /></template>
    </Button>
    <Button
      severity="danger"
      label="Stop"
      :disabled="disabled || !isRunning"
      title="Stop trading - also stops handling open trades."
      @click="handleStopBot()"
    >
      <template #icon><i-mdi-stop /></template>
    </Button>
    <Button
      severity="secondary"
      label="Reload config"
      :disabled="disabled"
      title="Reload config - reloads configuration including strategy, resetting all settings changed on the fly."
      @click="handleReloadConfig()"
    >
      <template #icon><i-mdi-reload /></template>
    </Button>
    <Button
      v-if="bot.botState?.force_entry_enable"
      severity="secondary"
      label="Force enter"
      :disabled="disabled || !isRunning"
      title="Force enter - immediately enter a trade at an optional price. Exits are then handled according to strategy rules."
      @click="forceEnter = true"
    >
      <template #icon><i-mdi-plus-box-multiple-outline /></template>
    </Button>
    <Button
      severity="danger"
      label="Force exit all"
      :disabled="disabled || bot.openTradeCount === 0"
      title="Force exit all open trades"
      @click="handleForceExit()"
    >
      <template #icon><i-mdi-close-box-multiple /></template>
    </Button>
    <ForceEntryForm v-model="forceEnter" :pair="bot.selectedPair" />
    <MessageBox ref="msgBox" />
  </div>
</template>

<style scoped>
.ft-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
</style>
