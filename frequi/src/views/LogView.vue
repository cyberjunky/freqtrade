<script setup lang="ts">
const botStore = useBotStore();
</script>

<template>
  <ToolPage title="Logs" description="Most recent log lines of the selected bot.">
    <FtPanel title="Log" flush body-height="calc(100dvh - 240px)" class="ft-logpanel">
      <LogViewer :key="botStore.selectedBot" />
    </FtPanel>
  </ToolPage>
</template>

<style scoped>
.ft-logpanel {
  min-height: 360px;
}
</style>
