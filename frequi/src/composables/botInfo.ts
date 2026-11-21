import type { Trade } from '@/types';
import { RunModes } from '@/types';
import type { BotSubStore } from '@/stores/ftbotwrapper';

export type BotUiState =
  | 'running'
  | 'paused'
  | 'stopped'
  | 'offline'
  | 'reloading'
  | 'webserver'
  | 'unknown';

export type BotUiMode = 'live' | 'dry' | 'webserver' | 'unknown';

export const BOT_SECTIONS = [
  { value: 'summary', label: 'Summary' },
  { value: 'chart', label: 'Chart' },
  { value: 'trades', label: 'Trades' },
  { value: 'performance', label: 'Performance' },
  { value: 'balance', label: 'Balance' },
  { value: 'bot', label: 'Bot' },
] as const;

export type BotSection = (typeof BOT_SECTIONS)[number]['value'];

/** Data is considered stale when an auto-refreshing bot did not answer for this long (ms). */
export const STALE_AFTER_MS = 45_000;

export function botUiState(bot: BotSubStore | undefined): BotUiState {
  if (!bot || !bot.isBotLoggedIn || !bot.isBotOnline) {
    return 'offline';
  }
  if (!bot.botStatusAvailable) {
    return 'unknown';
  }
  if (bot.isWebserverMode) {
    return 'webserver';
  }
  // The API may report states newer than the typed enum (e.g. "paused").
  const state = String(bot.botState?.state ?? '').toLowerCase();
  switch (state) {
    case 'running':
      return 'running';
    case 'paused':
      return 'paused';
    case 'stopped':
      return 'stopped';
    case 'reload_config':
      return 'reloading';
    default:
      return 'unknown';
  }
}

export function botUiMode(bot: BotSubStore | undefined): BotUiMode {
  if (!bot || !bot.botStatusAvailable) {
    return 'unknown';
  }
  if (bot.botState?.runmode === RunModes.WEBSERVER) {
    return 'webserver';
  }
  return bot.botState?.dry_run ? 'dry' : 'live';
}

export interface OpenProfit {
  abs: number;
  ratio: number | undefined;
  stake: number;
}

/** Unrealised (+ partially realised) profit of a set of open trades, stake weighted ratio. */
export function sumOpenProfit(trades: Trade[] | undefined): OpenProfit {
  if (!trades || trades.length === 0) {
    return { abs: 0, ratio: undefined, stake: 0 };
  }
  const stake = trades.reduce((a, b) => a + (b.stake_amount ?? 0), 0);
  const abs = trades.reduce((a, b) => a + (b.total_profit_abs ?? b.profit_abs ?? 0), 0);
  const ratio =
    stake > 0
      ? trades.reduce(
          (a, b) => a + (b.total_profit_ratio ?? b.profit_ratio ?? 0) * (b.stake_amount ?? 0),
          0,
        ) / stake
      : undefined;
  return { abs, ratio, stake };
}

/** Closed profit of "today" (latest entry of the daily stats, if it is today's date). */
export function profitToday(bot: BotSubStore | undefined): number | undefined {
  const data = bot?.dailyStats?.data;
  if (!data || data.length === 0) {
    return undefined;
  }
  const latest = data.reduce((a, b) => (a.date > b.date ? a : b));
  const today = timestampToDateString(Date.now());
  // Daily stats are aggregated in UTC on the bot side.
  const todayUtc = new Date().toISOString().substring(0, 10);
  if (latest.date === today || latest.date === todayUtc) {
    return latest.abs_profit;
  }
  return 0;
}

/**
 * Freshness of a bot's data. Returns undefined while data is fresh, otherwise
 * a message including the age - stale data must never be shown silently.
 */
export function useBotFreshness(bot: () => BotSubStore | undefined) {
  const now = useTimestamp({ interval: 1000 });

  const ageMs = computed(() => {
    const b = bot();
    if (!b || !b.lastUpdate) return undefined;
    return Math.max(0, now.value - b.lastUpdate);
  });

  const staleMessage = computed<string | undefined>(() => {
    const b = bot();
    if (!b) return undefined;
    const age = ageMs.value;
    const ageText = age === undefined ? 'no data received yet' : `data is ${formatAge(age)} old`;
    if (!b.isBotLoggedIn) {
      return `Login expired - ${ageText}. Log in again to resume updates.`;
    }
    if (!b.isBotOnline) {
      return `Bot offline - ${ageText}.`;
    }
    if (b.isWebserverMode) {
      return undefined;
    }
    if (!b.autoRefresh) {
      return `Auto-refresh is off - ${ageText}.`;
    }
    if (age !== undefined && age > STALE_AFTER_MS) {
      return `No update received - ${ageText}.`;
    }
    return undefined;
  });

  return { ageMs, staleMessage };
}
