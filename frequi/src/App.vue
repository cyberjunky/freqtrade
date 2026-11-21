<script setup lang="ts">
const settingsStore = useSettingsStore();

initTheme();

setTimezone(settingsStore.timezone);
watch(
  () => settingsStore.timezone,
  (tz) => setTimezone(tz),
);
</script>

<template>
  <div class="ft-app">
    <TopBar />
    <Toast position="top-right" />
    <main class="ft-main">
      <RouterView />
    </main>
    <StatusBar />
  </div>
</template>

<style scoped>
.ft-app {
  display: flex;
  flex-direction: column;
  height: 100dvh;
  min-width: 0;
}
.ft-main {
  flex: 1 1 auto;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
}
</style>
