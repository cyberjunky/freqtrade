<script setup lang="ts">
const botStore = useBotStore();
</script>

<template>
  <ToolPage
    title="Download data"
    description="Download historic candle data for backtesting."
    requires-webserver
    :feature-available="botStore.activeBotorUndefined?.botFeatures.downloadDataView ?? true"
  >
    <DownloadDataMain />
  </ToolPage>
</template>
