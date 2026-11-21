<script setup lang="ts">
const botStore = useBotStore();
const settingsStore = useSettingsStore();

const reachable = computed(() => botStore.allBotStores.filter((b) => b.isBotOnline).length);
const total = computed(() => botStore.botCount);

/** Websocket state over all trading bots (webserver mode bots have no websocket). */
const ws = computed(() => {
  const candidates = botStore.allBotStores.filter(
    (b) => b.isBotOnline && b.botStatusAvailable && !b.isWebserverMode,
  );
  const connected = candidates.filter((b) => b.websocketStarted).length;
  if (candidates.length === 0) {
    return { label: 'n/a', kind: 'idle' };
  }
  if (connected === candidates.length) {
    return { label: `connected ${connected}/${candidates.length}`, kind: 'ok' };
  }
  if (connected === 0) {
    return { label: 'off, polling', kind: 'idle' };
  }
  return { label: `connected ${connected}/${candidates.length}`, kind: 'warn' };
});

const apiVersion = computed(() => {
  const versions = new Set(
    botStore.allBotStores
      .filter((b) => b.botStatusAvailable)
      .map((b) => formatNumber(b.botApiVersion, 2)),
  );
  return versions.size ? Array.from(versions).join(' / ') : '-';
});

const botVersion = computed(() => {
  const versions = new Set(
    botStore.allBotStores.filter((b) => b.botStatusAvailable && b.version).map((b) => b.version),
  );
  return versions.size ? Array.from(versions).join(' / ') : '';
});

const reachKind = computed(() => {
  if (total.value === 0) return 'idle';
  if (reachable.value === total.value) return 'ok';
  return reachable.value === 0 ? 'bad' : 'warn';
});
</script>

<template>
  <footer class="ft-statusbar ft-mono" aria-label="Status">
    <span class="ft-sb-item" :title="`${reachable} of ${total} bots reachable`">
      <span class="ft-sb-dot" :class="`is-${reachKind}`" aria-hidden="true"></span>
      <span class="ft-sb-key">Bots</span> {{ reachable }}/{{ total }}
      <span class="ft-sb-wide">reachable</span>
    </span>
    <span
      class="ft-sb-item"
      title="WebSocket to the bots (live notifications, whitelist updates). When off, data is refreshed by polling."
    >
      <span class="ft-sb-dot" :class="`is-${ws.kind}`" aria-hidden="true"></span>
      <span class="ft-sb-key">WebSocket</span> {{ ws.label }}
    </span>
    <span v-if="!botStore.globalAutoRefresh && total > 0" class="ft-sb-item ft-sb-warn">
      auto-refresh paused
    </span>
    <span class="ft-sb-spacer"></span>
    <span v-if="botVersion" class="ft-sb-item ft-sb-wide" title="Freqtrade version">
      <span class="ft-sb-key">Bot</span> {{ botVersion }}
    </span>
    <!-- Versions are hidden on phones so the connection state stays readable. -->
    <span class="ft-sb-item ft-sb-wide" title="UI version">
      <span class="ft-sb-key">UI</span> {{ settingsStore.uiVersion }}
    </span>
    <span class="ft-sb-item ft-sb-wide" title="Bot API version">
      <span class="ft-sb-key">API</span> {{ apiVersion }}
    </span>
  </footer>
</template>

<style scoped>
.ft-statusbar {
  display: flex;
  align-items: center;
  gap: 18px;
  height: var(--ft-statusbar-h);
  padding: 0 20px;
  background: var(--ft-panel);
  border-top: 1px solid var(--ft-border);
  font-size: 11px;
  color: var(--ft-text-2);
  white-space: nowrap;
  overflow: hidden;
  flex: 0 0 auto;
}
.ft-sb-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ft-sb-key {
  color: var(--ft-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.ft-sb-spacer {
  flex: 1 1 auto;
}
.ft-sb-warn {
  color: var(--ft-warning);
}
.ft-sb-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--ft-idle);
  flex: 0 0 auto;
}
.ft-sb-dot.is-ok {
  background: var(--ft-success);
}
.ft-sb-dot.is-warn {
  background: var(--ft-warning);
}
.ft-sb-dot.is-bad {
  background: var(--ft-danger);
}
@media (max-width: 700px) {
  .ft-statusbar {
    padding: 0 12px;
    gap: 12px;
  }
  .ft-sb-wide {
    display: none;
  }
}
</style>
