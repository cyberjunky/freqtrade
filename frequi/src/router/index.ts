import type { RouteLocationRaw, RouteRecordRaw } from 'vue-router';
import { createRouter, createWebHistory } from 'vue-router';
import type { BotSection } from '@/composables/botInfo';

/** Route to a section of the currently selected (or first) bot - used by the legacy paths. */
function botRoute(section: BotSection): RouteLocationRaw {
  const botStore = useBotStore();
  const botId = botStore.selectedBot || botStore.availableBotsSorted[0]?.botId;
  if (!botId) {
    return { name: 'Overview' };
  }
  return { name: 'Bot', params: { botId, section }, replace: true };
}

/** Old paths keep working: they forward to the matching section of the bot page. */
function legacy(path: string, section: BotSection): RouteRecordRaw {
  return {
    path,
    component: () => import('@/views/BotView.vue'),
    beforeEnter: () => botRoute(section),
  };
}

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'Overview',
    component: () => import('@/views/OverviewView.vue'),
    meta: {
      allowAnonymous: true,
    },
  },
  {
    path: '/bot/:botId/:section(summary|chart|trades|performance|balance|bot)?',
    name: 'Bot',
    component: () => import('@/views/BotView.vue'),
  },
  // Legacy paths (pre-redesign) -> redirects
  { path: '/dashboard', redirect: { name: 'Overview' } },
  legacy('/trade', 'summary'),
  legacy('/graph', 'chart'),
  legacy('/balance', 'balance'),
  legacy('/open_trades', 'summary'),
  legacy('/trade_history', 'trades'),
  legacy('/pairlist', 'bot'),
  // Tools
  {
    path: '/logs',
    name: 'Freqtrade Logs',
    component: () => import('@/views/LogView.vue'),
  },
  {
    path: '/backtest',
    name: 'Freqtrade Backtest',
    component: () => import('@/views/BacktestingView.vue'),
  },
  {
    path: '/settings',
    name: 'Freqtrade Settings',
    component: () => import('@/views/SettingsView.vue'),
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: {
      allowAnonymous: true,
    },
  },
  {
    path: '/pairlist_config',
    name: 'Pairlist Configuration',
    component: () => import('@/views/PairlistConfigView.vue'),
  },
  {
    path: '/download_data',
    name: 'Download Data',
    component: () => import('@/views/DownloadDataView.vue'),
  },
  {
    path: '/(.*)*',
    name: '404',
    component: () => import('@/views/Error404View.vue'),
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

router.beforeEach((to) => {
  // Init bots here...
  initBots();
  const botStore = useBotStore();
  if (!to.meta?.allowAnonymous && !botStore.hasBots) {
    // Forward to login if login is required
    return {
      path: '/login',
      query: { redirect: to.fullPath },
    };
  }
  if (to.name === 'Bot') {
    const botId = String(to.params.botId);
    if (!(botId in botStore.availableBots)) {
      return { name: 'Overview' };
    }
    if (botStore.selectedBot !== botId) {
      botStore.selectBot(botId);
    }
  }
  return true;
});

export default router;
