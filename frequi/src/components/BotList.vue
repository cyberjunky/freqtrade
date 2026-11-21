<script setup lang="ts">
import LoginModal from '@/components/LoginModal.vue';

import type { AuthStorageWithBotId, BotDescriptor } from '@/types';
import { useSortable } from '@vueuse/integrations/useSortable';

defineProps<{
  small?: boolean;
}>();

const botStore = useBotStore();

const editingBots = ref<string[]>([]);
const loginModal = ref<typeof LoginModal>();
const sortContainer = ref<HTMLElement | null>(null);
const botListComp = computed<BotDescriptor[]>(() => {
  //Convert to array
  return botStore.availableBotsSorted;
});

useSortable(sortContainer, botListComp, {
  handle: '.handle',
  onUpdate: (e) => {
    if (e.oldIndex === undefined || e.newIndex === undefined) {
      return;
    }
    const oldBotId = botListComp.value[e.oldIndex]?.botId;
    const newBotId = botListComp.value[e.newIndex]?.botId;
    if (oldBotId && newBotId) {
      botStore.updateBot(oldBotId, { sortId: e.newIndex });
      botStore.updateBot(newBotId, { sortId: e.oldIndex });
    }
  },
});

function editBot(botId: string) {
  if (!editingBots.value.includes(botId)) {
    editingBots.value.push(botId);
  }
}

function editBotLogin(botId: string) {
  const bot = botStore.botStores[botId];
  if (!bot) {
    console.error('Bot not found');
    return;
  }
  const loginInfo: AuthStorageWithBotId = {
    ...bot.getLoginInfo(),
    botId,
  };
  loginModal.value?.openLoginModal(loginInfo);
}

function stopEditBot(botId: string) {
  if (!editingBots.value.includes(botId)) {
    return;
  }

  editingBots.value.splice(editingBots.value.indexOf(botId), 1);
}
</script>

<template>
  <div v-if="botStore.botCount > 0" class="ft-botlist">
    <ul ref="sortContainer" class="ft-botlist-items">
      <li
        v-for="bot in botListComp"
        :key="bot.botId"
        :title="`${bot.botId} - ${bot.botName} - ${bot.botUrl} ${
          botStore.botStores[bot.botId]?.isBotLoggedIn ? '' : '- Login info expired!'
        }`"
        class="ft-botlist-item"
      >
        <i-mdi-drag
          v-if="!small"
          class="handle ft-botlist-handle"
          title="Drag to reorder"
          aria-hidden="true"
        />
        <BotRename
          v-if="editingBots.includes(bot.botId)"
          :bot="bot"
          @saved="stopEditBot(bot.botId)"
          @cancelled="stopEditBot(bot.botId)"
        />

        <BotEntry
          v-else
          :bot="bot"
          :no-buttons="small"
          @edit="editBot(bot.botId)"
          @edit-login="editBotLogin(bot.botId)"
        />
      </li>
    </ul>
    <LoginModal v-if="!small" ref="loginModal" class="ft-botlist-add" login-text="Add new bot" />
  </div>
</template>

<style scoped>
.ft-botlist-items {
  list-style: none;
  margin: 0;
  padding: 0;
  border: 1px solid var(--ft-border);
  border-radius: var(--ft-radius-control);
}
.ft-botlist-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  border-bottom: 1px solid var(--ft-border);
  min-width: 0;
}
.ft-botlist-item:last-child {
  border-bottom: 0;
}
.ft-botlist-handle {
  cursor: grab;
  color: var(--ft-muted);
  flex: 0 0 auto;
}
.ft-botlist-add {
  margin-top: 10px;
}
</style>
