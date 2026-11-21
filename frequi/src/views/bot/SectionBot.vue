<script setup lang="ts">
const botStore = useBotStore();
const bot = computed(() => botStore.activeBot);
</script>

<template>
  <div class="ft-stack">
    <div class="ft-grid-2">
      <FtPanel title="Status and config">
        <BotStatus />
      </FtPanel>
      <FtPanel v-if="!bot.isWebserverMode" title="Trading rules">
        <BotRules />
      </FtPanel>
    </div>

    <FtPanel v-if="bot.strategy?.params?.length" title="Strategy parameters">
      <StrategyParameters :strategy="bot.strategy" />
    </FtPanel>

    <template v-if="!bot.isWebserverMode">
      <FtPanel title="Pair locks" flush>
        <template #actions>
          <Button
            size="small"
            severity="secondary"
            title="Refresh locks"
            aria-label="Refresh locks"
            @click="bot.getLocks()"
          >
            <template #icon><i-mdi-refresh /></template>
          </Button>
        </template>
        <PairLockList />
      </FtPanel>

      <FtPanel title="Pairlist">
        <PairListLive />
      </FtPanel>
    </template>

    <FtPanel title="Log" flush body-height="460px">
      <LogViewer />
    </FtPanel>
  </div>
</template>
