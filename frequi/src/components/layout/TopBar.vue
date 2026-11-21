<script setup lang="ts">
import Menu from 'primevue/menu';
import type { MenuItem } from 'primevue/menuitem';
import type MessageBox from '@/components/general/MessageBox.vue';
import type LoginModal from '@/components/LoginModal.vue';

const botStore = useBotStore();
const settingsStore = useSettingsStore();
const route = useRoute();
const router = useRouter();

useTitleAndFavicon();

const { mode: themeMode, cycle: cycleTheme } = useThemeMode();

const pingInterval = ref<number>();
onMounted(async () => {
  await settingsStore.loadUIVersion();
  pingInterval.value = window.setInterval(botStore.pingAll, 60000);
});
onBeforeUnmount(() => {
  if (pingInterval.value) {
    clearInterval(pingInterval.value);
  }
});

// ---- Navigation -------------------------------------------------------------
const TOOL_ROUTES = ['/backtest', '/pairlist_config', '/download_data', '/logs', '/settings'];

const activeTab = computed<string>(() => {
  if (route.name === 'Overview') return 'overview';
  if (route.name === 'Bot') return String(route.params.botId ?? '');
  if (TOOL_ROUTES.some((p) => route.path.startsWith(p))) return 'tools';
  return '';
});

const botTabs = computed(() =>
  botStore.availableBotsSorted.map((bot) => {
    const store = botStore.botStores[bot.botId];
    return {
      botId: bot.botId,
      name: store?.uiBotName || bot.botName || bot.botId,
      state: botUiState(store),
      mode: botUiMode(store),
    };
  }),
);

const toolsMenu = ref<InstanceType<typeof Menu> | null>();
const toolItems = computed<MenuItem[]>(() => [
  { label: 'Backtesting', command: () => router.push('/backtest') },
  { label: 'Pairlist config', command: () => router.push('/pairlist_config') },
  { label: 'Download data', command: () => router.push('/download_data') },
  { label: 'Logs', command: () => router.push('/logs') },
  { separator: true },
  { label: 'Settings', command: () => router.push('/settings') },
]);

// ---- Clock ------------------------------------------------------------------
const now = useNow({ interval: 1000 });
const clock = computed(() => {
  // Recomputed every second, picks up timezone changes from the settings.
  const tz = settingsStore.timezone;
  const text = timestampms(now.value).substring(11);
  return { text, tz: tz === 'UTC' ? 'UTC' : 'local' };
});

// ---- Theme ------------------------------------------------------------------
const themeLabel = computed(
  () => THEME_MODES.find((m) => m.value === themeMode.value)?.label ?? 'Auto',
);

// ---- Account ----------------------------------------------------------------
const accountMenu = ref<InstanceType<typeof Menu> | null>();
const msgBox = ref<InstanceType<typeof MessageBox>>();
const loginModal = ref<InstanceType<typeof LoginModal>>();

function logout(botId: string) {
  const name = botStore.botStores[botId]?.uiBotName ?? botId;
  msgBox.value?.show({
    title: 'Logout',
    message: `Log out of ${name}? The bot keeps running, only this browser forgets the login.`,
    confirmLabel: 'Logout',
    accept: async () => {
      botStore.removeBot(botId);
      await router.push('/');
    },
  });
}

const accountItems = computed<MenuItem[]>(() => {
  const items: MenuItem[] = [
    { label: `UI ${settingsStore.uiVersion}`, disabled: true },
    { label: 'Settings', command: () => router.push('/settings') },
    { label: 'Add bot', command: () => loginModal.value?.openLoginModal() },
    { separator: true },
  ];
  if (botStore.botCount === 1) {
    items.push({ label: 'Logout', command: () => logout(botStore.selectedBot) });
  } else {
    botStore.availableBotsSorted.forEach((bot) => {
      items.push({
        label: `Logout ${bot.botName || bot.botId}`,
        command: () => logout(bot.botId),
      });
    });
  }
  return items;
});
</script>

<template>
  <header class="ft-topbar">
    <RouterLink class="ft-brand" to="/" aria-label="Freqtrade - Overview">
      <i-mdi-chart-line class="ft-brand-icon" aria-hidden="true" />
      <span class="ft-brand-text">FREQTRADE</span>
    </RouterLink>

    <nav class="ft-topnav" aria-label="Main">
      <div v-if="botStore.hasBots" class="ft-seg" role="tablist" aria-label="Views">
        <RouterLink
          to="/"
          class="ft-seg-tab"
          :class="{ 'is-active': activeTab === 'overview' }"
          role="tab"
          :aria-selected="activeTab === 'overview'"
          >Overview</RouterLink
        >
        <RouterLink
          v-for="bot in botTabs"
          :key="bot.botId"
          :to="{ name: 'Bot', params: { botId: bot.botId } }"
          class="ft-seg-tab ft-bot-tab"
          :class="[`is-${bot.state}`, { 'is-active': activeTab === bot.botId }]"
          role="tab"
          :aria-selected="activeTab === bot.botId"
          :title="`${bot.name} - ${bot.state}, ${bot.mode === 'live' ? 'LIVE' : bot.mode === 'dry' ? 'dry-run' : bot.mode}`"
        >
          <span class="ft-bot-dot" aria-hidden="true"></span>
          <span>{{ bot.name }}</span>
          <span v-if="bot.mode === 'live'" class="ft-bot-live">LIVE</span>
        </RouterLink>
        <button
          type="button"
          class="ft-seg-tab"
          :class="{ 'is-active': activeTab === 'tools' }"
          aria-haspopup="menu"
          @click="toolsMenu?.toggle($event)"
        >
          Tools <i-mdi-chevron-down aria-hidden="true" />
        </button>
      </div>
      <span v-else class="ft-nobot">No bot selected</span>
      <Menu ref="toolsMenu" :model="toolItems" popup />
    </nav>

    <div class="ft-topright">
      <FtBadge
        v-if="!settingsStore.confirmDialog"
        kind="warn"
        title="Confirm dialog deactivated - force exits will be executed immediately. Change this in Settings."
      >
        <i-mdi-alert aria-hidden="true" /> NO CONFIRM
      </FtBadge>
      <Button
        v-if="botStore.hasBots"
        severity="secondary"
        variant="text"
        title="Refresh all bots now"
        aria-label="Refresh all bots now"
        :disabled="botStore.refreshing"
        @click="botStore.allRefreshFull()"
      >
        <template #icon><i-mdi-refresh :class="{ 'ft-spin': botStore.refreshing }" /></template>
      </Button>
      <Button
        severity="secondary"
        variant="text"
        class="ft-theme-btn"
        :title="`Theme: ${themeLabel} (click to change)`"
        :aria-label="`Theme: ${themeLabel}`"
        @click="cycleTheme"
      >
        <i-mdi-theme-light-dark v-if="themeMode === 'auto'" aria-hidden="true" />
        <i-mdi-white-balance-sunny v-else-if="themeMode === 'light'" aria-hidden="true" />
        <i-mdi-weather-night v-else aria-hidden="true" />
        <span class="ft-theme-label">{{ themeLabel }}</span>
      </Button>
      <span class="ft-clock ft-mono" :title="`Time (${clock.tz})`"
        >{{ clock.text }} <span class="ft-clock-tz">{{ clock.tz }}</span></span
      >
      <template v-if="botStore.hasBots">
        <Button
          severity="secondary"
          aria-label="Account"
          title="Account"
          aria-haspopup="menu"
          @click="accountMenu?.toggle($event)"
        >
          <template #icon><i-mdi-account-circle-outline /></template>
        </Button>
        <Menu ref="accountMenu" :model="accountItems" popup />
        <LoginModal ref="loginModal" hide-button />
      </template>
      <LoginModal v-else-if="route.path !== '/login'" />
    </div>
    <MessageBox ref="msgBox" />
  </header>
</template>

<style scoped>
.ft-topbar {
  display: flex;
  align-items: center;
  gap: 8px 18px;
  min-height: var(--ft-topbar-h);
  padding: 0 20px;
  background: var(--ft-panel);
  border-bottom: 1px solid var(--ft-border);
  flex: 0 0 auto;
}
.ft-brand {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--ft-text);
  text-decoration: none;
  font-weight: 600;
  letter-spacing: 0.12em;
  font-size: 13px;
  flex: 0 0 auto;
}
.ft-brand-icon {
  color: var(--ft-primary);
  font-size: 18px;
}
.ft-topnav {
  flex: 1 1 auto;
  min-width: 0;
  display: flex;
  align-items: center;
}
.ft-nobot {
  color: var(--ft-muted);
  font-size: 12.5px;
}
.ft-bot-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--ft-idle);
  flex: 0 0 auto;
}
.ft-bot-tab.is-running .ft-bot-dot {
  background: var(--ft-success);
}
.ft-bot-tab.is-paused .ft-bot-dot,
.ft-bot-tab.is-reloading .ft-bot-dot {
  background: var(--ft-warning);
}
.ft-bot-tab.is-stopped .ft-bot-dot {
  background: var(--ft-danger);
}
.ft-bot-tab.is-webserver .ft-bot-dot {
  background: var(--ft-primary);
}
.ft-bot-tab.is-active .ft-bot-dot {
  box-shadow: 0 0 0 1.5px var(--ft-on-primary);
}
.ft-bot-live {
  font-size: 9.5px;
  font-weight: 600;
  letter-spacing: 0.06em;
  padding: 0 4px;
  border-radius: var(--ft-radius-badge);
  background: var(--ft-warning-bg);
  color: var(--ft-warning);
}
.ft-bot-tab.is-active .ft-bot-live {
  background: var(--ft-on-primary);
  color: var(--ft-primary);
}
.ft-topright {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 0 0 auto;
  margin-left: auto;
}
.ft-theme-label {
  font-size: 12px;
}
.ft-clock {
  font-size: 12.5px;
  color: var(--ft-text);
  white-space: nowrap;
  padding: 0 4px;
}
.ft-clock-tz {
  color: var(--ft-muted);
  font-size: 11px;
}
.ft-spin {
  animation: ft-spin 0.9s linear infinite;
}
@keyframes ft-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1000px) {
  .ft-theme-label,
  .ft-clock-tz {
    display: none;
  }
}

@media (max-width: 700px) {
  .ft-topbar {
    flex-wrap: wrap;
    padding: 8px 12px;
    gap: 8px 10px;
  }
  .ft-topnav {
    order: 3;
    flex: 1 1 100%;
  }
  .ft-topnav .ft-seg {
    width: 100%;
  }
}
</style>
