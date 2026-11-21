<script setup lang="ts">
/**
 * Page frame for the Tools pages: title, the bot the tool talks to (with a
 * selector when several bots are configured) and an optional mode requirement.
 */
const props = withDefaults(
  defineProps<{
    title: string;
    description?: string;
    /** Tool only works with a bot started in webserver mode */
    requiresWebserver?: boolean;
    /** Feature the bot must support (by API version) */
    featureAvailable?: boolean;
    /** Use the full width instead of the 1500px container */
    wide?: boolean;
  }>(),
  { description: '', requiresWebserver: false, featureAvailable: true, wide: false },
);

const botStore = useBotStore();
const bot = computed(() => botStore.activeBotorUndefined);

const botOptions = computed(() =>
  botStore.availableBotsSorted.map((b) => {
    const store = botStore.botStores[b.botId];
    const mode = botUiMode(store);
    return {
      value: b.botId,
      label: `${store?.uiBotName || b.botName || b.botId}`,
      mode,
    };
  }),
);

const blocked = computed<string | undefined>(() => {
  if (!bot.value) return 'No bot selected.';
  if (!bot.value.isBotOnline) return `${bot.value.uiBotName} is offline.`;
  if (!bot.value.botStatusAvailable) return undefined; // still loading
  if (props.requiresWebserver && !bot.value.isWebserverMode) {
    return `${props.title} needs a bot started in webserver mode ("freqtrade webserver"). ${bot.value.uiBotName} is a trading bot.`;
  }
  if (!props.featureAvailable) {
    return `${bot.value.uiBotName} runs a Freqtrade version that does not support this.`;
  }
  return undefined;
});
</script>

<template>
  <div class="ft-container ft-stack" :class="{ 'is-wide': wide }">
    <div class="ft-toolhead">
      <div class="ft-toolhead-title">
        <h1 class="ft-page-title">{{ title }}</h1>
        <p v-if="description" class="ft-hint">{{ description }}</p>
      </div>
      <div v-if="bot" class="ft-toolhead-bot">
        <span class="ft-hint">Bot</span>
        <Select
          v-if="botStore.botCount > 1"
          :model-value="botStore.selectedBot"
          :options="botOptions"
          option-label="label"
          option-value="value"
          size="small"
          aria-label="Bot used by this tool"
          class="ft-toolhead-select"
          @update:model-value="botStore.selectBot($event)"
        />
        <strong v-else>{{ bot.uiBotName }}</strong>
        <FtState :state="botUiState(bot)" />
        <FtMode v-if="!bot.isWebserverMode" :mode="botUiMode(bot)" />
        <slot name="actions" />
      </div>
    </div>
    <FtPanel v-if="blocked">
      <FtEmpty :title="`${title} is not available`" :text="blocked">
        <template #icon><i-mdi-information-outline /></template>
      </FtEmpty>
    </FtPanel>
    <slot v-else />
  </div>
</template>

<style scoped>
.is-wide {
  max-width: none;
}
.ft-toolhead {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px 18px;
}
.ft-toolhead-title .ft-hint {
  margin: 2px 0 0;
}
.ft-toolhead-bot {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 10px;
}
.ft-toolhead-select {
  min-width: 160px;
}
</style>
