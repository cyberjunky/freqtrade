<script setup lang="ts">
const botStore = useBotStore();
const scrollContainer = ref<HTMLElement | null>(null);

onMounted(async () => {
  refreshLogs();
});

async function refreshLogs() {
  await botStore.activeBot.getLogs();
  scrollToBottom();
}

function getLogColor(logLevel: string) {
  switch (logLevel) {
    case 'WARNING':
      return 'is-warn';
    case 'ERROR':
      return 'is-error';
    default:
      return '';
  }
}

function scrollToBottom() {
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight;
  }
}
</script>

<template>
  <div class="ft-log">
    <div class="ft-log-bar">
      <span class="ft-hint ft-mono">{{ botStore.activeBot.lastLogs.length }} lines</span>
      <div class="flex gap-2">
        <Button
          id="refresh-logs"
          severity="secondary"
          size="small"
          label="Reload"
          title="Reload Logs"
          aria-label="Reload Logs"
          @click="refreshLogs"
        >
          <template #icon><i-mdi-refresh /></template>
        </Button>
        <Button
          size="small"
          title="Scroll to bottom"
          aria-label="Scroll to bottom"
          severity="secondary"
          @click="scrollToBottom"
        >
          <template #icon><i-mdi-arrow-down-thick /></template>
        </Button>
      </div>
    </div>
    <div ref="scrollContainer" class="ft-log-body ft-mono" tabindex="0">
      <pre
        v-for="(log, index) in botStore.activeBot.lastLogs"
        :key="index"
        class="ft-log-line"
      ><span class="ft-dim">{{ log[0] }} <span :class="getLogColor(log[3])">{{ log[3].padEnd(7, ' ') }}</span> {{ log[2] }} - </span
      ><span>{{ log[4] }}</span
        ></pre>
      <FtEmpty v-if="botStore.activeBot.lastLogs.length === 0" title="No log lines" />
    </div>
  </div>
</template>

<style lang="css" scoped>
.ft-log {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}
.ft-log-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid var(--ft-border);
}
.ft-log-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
  padding: 10px 12px;
  font-size: 12px;
  background: var(--ft-page);
  border-radius: 0 0 var(--ft-radius-panel) var(--ft-radius-panel);
}
.ft-log-line {
  margin: 0;
  font-family: inherit;
  line-height: 1.5;
  white-space: pre;
}
.is-warn {
  color: var(--ft-warning);
}
.is-error {
  color: var(--ft-danger);
}
</style>
