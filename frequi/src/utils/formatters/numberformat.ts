export function isNotUndefined<T>(val: T | undefined | null): val is T {
  return !(val === undefined || val === null);
}

export function formatPercent(value: number | undefined | null, decimals = 3): string {
  return isNotUndefined(value)
    ? `${(value * 100).toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}%`
    : 'N/A%';
}

/**
 * Format number to `decimals` without trailing zeros
 * @param value Number to format
 * @param decimals number of decimals (Defaults to 15)
 * @returns Formatted string
 */
export function formatNumber(value: number | null | undefined, decimals = 15): string {
  // const format = new Intl.NumberFormat('', {maximumFractionDigits: decimals}
  return isNotUndefined(value)
    ? value.toLocaleString('fullwide', {
        useGrouping: false,
        maximumFractionDigits: decimals,
      })
    : 'N/A';
}

/**
 * Format number to `decimals` without trailing zeros
 * Compatibility function
 * // TODO: should be replaced with formatNumber!
 * @param value Number to format
 * @param decimals number of decimals (Defaults to 15)
 * @returns Formatted string
 */
export function formatPrice(value: number | null, decimals = 15): string {
  return formatNumber(value, decimals);
}

/**
 * Formats price in the format "<price> <StakeCurrency>" using "deciaml" decimals
 * @param price Price to format
 * @param currency currency to use
 * @param decimals Decimals
 * @returns
 */
export function formatPriceCurrency(price: number | null, currency: string, decimals = 3) {
  return `${formatPrice(price, decimals)} ${currency ?? ''}`;
}

/**
 * Formats a decimal number to a string with a varying number of decimal places
 * depending on the size of the number.
 * @param value Number to format
 * @returns Formatted string
 */
export function formatDecimal(value: number | null): string {
  if (!isNotUndefined(value)) {
    return 'N/A';
  }
  let decimals = 2;
  const absValue = Math.abs(value);
  if (absValue < 0.0000001) {
    decimals = 15;
  } else if (absValue < 0.000001) {
    decimals = 11;
  } else if (absValue < 0.0001) {
    decimals = 8;
  } else if (absValue < 0.01) {
    decimals = 5;
  } else if (absValue < 1) {
    decimals = 5;
  } else if (absValue < 10) {
    decimals = 4;
  } else if (absValue < 100) {
    decimals = 3;
  }
  return value.toLocaleString('fullwide', {
    useGrouping: false,
    maximumFractionDigits: decimals,
  });
}

/**
 * Sign prefix for a profit / loss value. Profit and loss always carry a sign.
 */
export function signOf(value: number | undefined | null): string {
  if (!isNotUndefined(value) || value === 0 || Number.isNaN(value)) {
    return '';
  }
  return value > 0 ? '+' : '';
}

/** Format a number with explicit sign (+1.23 / -1.23 / 0). */
export function formatSigned(value: number | undefined | null, decimals = 3): string {
  return isNotUndefined(value) ? `${signOf(value)}${formatNumber(value, decimals)}` : 'N/A';
}

/** Format a ratio as percent with explicit sign (+1.23% / -1.23% / 0.00%). */
export function formatSignedPercent(value: number | undefined | null, decimals = 2): string {
  return isNotUndefined(value) ? `${signOf(value)}${formatPercent(value, decimals)}` : 'N/A';
}

/** CSS class for a profit value: ft-pos / ft-neg / ft-dim (zero or unknown). */
export function profitClass(value: number | undefined | null): string {
  if (!isNotUndefined(value) || value === 0 || Number.isNaN(value)) {
    return 'ft-dim';
  }
  return value > 0 ? 'ft-pos' : 'ft-neg';
}

/** Short human readable age ("12s", "4m", "3h", "2d") for a duration in ms. */
export function formatAge(ms: number): string {
  const s = Math.max(0, Math.round(ms / 1000));
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 48) return `${h}h`;
  return `${Math.floor(h / 24)}d`;
}
