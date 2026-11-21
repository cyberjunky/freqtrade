<script setup lang="ts">
import type { BotDescriptor } from '@/types';
import type MessageBox from './general/MessageBox.vue';
const msgBox = ref<typeof MessageBox>();

const props = defineProps<{
  bot: BotDescriptor;
  noButtons?: boolean;
}>();
defineEmits<{ edit: []; editLogin: [] }>();
const botStore = useBotStore();

function confirmRemoveBot() {
  botStore.removeBot(props.bot.botId);
}

function removeBotQuestion() {
  msgBox.value?.show({
    title: 'Logout confirmation',
    message: `Really remove (logout) from ${props.bot.botName} (${props.bot.botId})?`,
    accept: () => {
      confirmRemoveBot();
    },
  });
}

const selectedBotStore = computed<BotSubStore>(() => {
  return botStore.botStores[props.bot.botId]!;
});

const autoRefreshLoc = computed({
  get() {
    return selectedBotStore.value.autoRefresh;
  },
  set(newValue) {
    selectedBotStore.value.setAutoRefresh(newValue);
  },
});
</script>

<template>
  <div v-if="bot" class="ft-botentry">
    <span class="ft-botentry-name">{{ bot.botName || bot.botId }}</span>
    <FtState :state="botUiState(selectedBotStore)" />
    <FtMode :mode="botUiMode(selectedBotStore)" />
    <span class="ft-botentry-url ft-mono ft-dim">{{ bot.botUrl }}</span>

    <div class="ft-botentry-actions">
      <label class="ft-botentry-refresh" title="Auto-refresh this bot">
        <ToggleSwitch v-model="autoRefreshLoc" aria-label="Auto-refresh" />
        <span>Auto-refresh</span>
      </label>
      <FtBadge
        v-if="!selectedBotStore.isBotLoggedIn"
        kind="bad"
        title="Login info expired, please login again."
        >LOGIN EXPIRED</FtBadge
      >
      <template v-if="!noButtons">
        <Button
          v-if="selectedBotStore.isBotLoggedIn"
          size="small"
          severity="secondary"
          title="Rename bot"
          aria-label="Rename bot"
          @click.stop="$emit('edit')"
        >
          <template #icon><i-mdi-pencil /></template>
        </Button>
        <Button
          v-else
          size="small"
          severity="secondary"
          label="Login again"
          @click.stop="$emit('editLogin')"
        >
          <template #icon><i-mdi-login /></template>
        </Button>
        <Button
          size="small"
          severity="danger"
          title="Remove bot (logout)"
          aria-label="Remove bot"
          @click.stop="removeBotQuestion"
        >
          <template #icon><i-mdi-delete /></template>
        </Button>
      </template>
    </div>
    <MessageBox ref="msgBox" />
  </div>
</template>

<style scoped>
.ft-botentry {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 12px;
  width: 100%;
  min-width: 0;
}
.ft-botentry-name {
  font-weight: 600;
}
.ft-botentry-url {
  font-size: 11.5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}
.ft-botentry-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}
.ft-botentry-refresh {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--ft-text-2);
  cursor: pointer;
}
@media (max-width: 700px) {
  .ft-botentry-refresh span {
    display: none;
  }
}
</style>
