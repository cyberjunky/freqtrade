<script setup lang="ts">
const botStore = useBotStore();
</script>

<template>
  <ToolPage
    title="Pairlist config"
    description="Compose pairlist handlers and evaluate the resulting whitelist."
    requires-webserver
    :feature-available="botStore.activeBotorUndefined?.botFeatures.pairlistConfig ?? true"
  >
    <PairlistConfigurator />
  </ToolPage>
</template>
