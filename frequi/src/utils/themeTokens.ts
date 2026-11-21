/**
 * Reads design tokens from CSS (styles/tokens.css) so JS consumers (ECharts)
 * use the very same values as the stylesheet. No colour is defined here.
 */

export type ThemeKind = 'dark' | 'light';

const TOKEN_NAMES = [
  'page',
  'panel',
  'text',
  'text-2',
  'muted',
  'primary',
  'warning',
  'success',
  'danger',
  'border',
  'grid',
  'hover',
  'selected',
  'pos',
  'neg',
  'idle',
  'series-1',
  'series-2',
  'series-3',
  'series-4',
  'series-5',
  'series-wash',
  'font-sans',
  'font-mono',
] as const;

type TokenName = (typeof TOKEN_NAMES)[number];

export type ThemeTokens = Record<TokenName, string> & { series: string[] };

function emptyTokens(): ThemeTokens {
  const res = { series: [] as string[] } as ThemeTokens;
  TOKEN_NAMES.forEach((n) => (res[n] = ''));
  return res;
}

/** Read the tokens of one theme, independent of the theme currently applied. */
export function readThemeTokens(theme: ThemeKind): ThemeTokens {
  const res = emptyTokens();
  if (typeof document === 'undefined' || !document.body) {
    return res;
  }
  const probe = document.createElement('div');
  probe.className = theme === 'dark' ? 'ft-dark-theme' : 'ft-light-theme';
  probe.style.display = 'none';
  document.body.appendChild(probe);
  const style = getComputedStyle(probe);
  TOKEN_NAMES.forEach((n) => {
    res[n] = style.getPropertyValue(`--ft-${n}`).trim();
  });
  probe.remove();
  res.series = [
    res['series-1'],
    res['series-2'],
    res['series-3'],
    res['series-4'],
    res['series-5'],
  ];
  return res;
}

/** Tokens of the currently active theme - reactive, refreshed on theme change. */
export const themeTokens = reactive<ThemeTokens>(emptyTokens());

export function refreshThemeTokens(theme: ThemeKind) {
  Object.assign(themeTokens, readThemeTokens(theme));
}
