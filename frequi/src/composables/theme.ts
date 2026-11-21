import type { ThemeKind } from '@/utils/themeTokens';

export type ThemeMode = 'auto' | 'light' | 'dark';

export const THEME_MODES: { value: ThemeMode; label: string }[] = [
  { value: 'auto', label: 'Auto' },
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' },
];

/** Apply a resolved theme to the document (classes used by tokens.css, Tailwind and PrimeVue). */
export function applyThemeClasses(theme: ThemeKind, animate = false) {
  const root = document.documentElement;
  if (animate) {
    document.body.classList.add('ft-theme-transition');
    window.setTimeout(() => document.body.classList.remove('ft-theme-transition'), 300);
  }
  root.classList.toggle('dark', theme === 'dark');
  root.classList.toggle('ft-dark-theme', theme === 'dark');
  root.classList.toggle('ft-light-theme', theme === 'light');
  refreshThemeTokens(theme);
}

/**
 * Theme handling: auto / light / dark, persisted in the settings store.
 * Call `initTheme()` once (App.vue); use `useThemeMode()` anywhere for the toggle.
 */
export function useThemeMode() {
  const settingsStore = useSettingsStore();
  const prefersDark = usePreferredDark();

  const mode = computed<ThemeMode>({
    get: () => {
      if (settingsStore.themeMode) return settingsStore.themeMode;
      // Migrate from the old light/dark-only setting
      return settingsStore.isDarkTheme ? 'dark' : 'light';
    },
    set: (val) => {
      settingsStore.themeMode = val;
    },
  });

  const resolved = computed<ThemeKind>(() => {
    if (mode.value === 'auto') {
      return prefersDark.value ? 'dark' : 'light';
    }
    return mode.value;
  });

  function cycle() {
    const order: ThemeMode[] = ['auto', 'light', 'dark'];
    mode.value = order[(order.indexOf(mode.value) + 1) % order.length] ?? 'auto';
  }

  return { mode, resolved, cycle };
}

export function initTheme() {
  const settingsStore = useSettingsStore();
  const { resolved } = useThemeMode();
  let first = true;
  watch(
    resolved,
    (theme) => {
      applyThemeClasses(theme, !first);
      first = false;
      // Keep the legacy setting in sync - charts read `chartTheme` derived from it.
      settingsStore.currentTheme = theme;
    },
    { immediate: true },
  );
}
