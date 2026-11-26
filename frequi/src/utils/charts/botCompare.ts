import type { ClosedTrade, MarketReference, WalletHistory } from '@/types';

/** [timestamp_ms, value] */
export type Point = [number, number];

const HOUR = 3_600_000;

/** Hourly equity (balance incl. open positions) from /historic_balance, sorted by time. */
export function equityPoints(history: WalletHistory): Point[] {
  const colDate = history.columns.indexOf('__date_ts');
  const colTotal = history.columns.indexOf('total_quote');
  if (colDate < 0 || colTotal < 0) return [];
  return history.data
    .map((row) => [Number(row[colDate]), Number(row[colTotal])] as Point)
    .filter(([t, v]) => Number.isFinite(t) && Number.isFinite(v))
    .sort((a, b) => a[0] - b[0]);
}

/** Equity from closed trades only: starting capital plus realised profit, stepping at each close. */
export function closedPoints(trades: ClosedTrade[], start: number, startCapital: number): Point[] {
  let equity = startCapital;
  const res: Point[] = [[start, equity]];
  [...trades]
    .filter((t) => t.close_timestamp)
    .sort((a, b) => a.close_timestamp - b.close_timestamp)
    .forEach((t) => {
      equity += t.profit_abs ?? 0;
      res.push([Math.max(t.close_timestamp, start), equity]);
    });
  return res;
}

/** Value of a step series at `ts`: the last point at or before it, else the first point. */
export function valueAt(points: Point[], ts: number): number | undefined {
  if (points.length === 0) return undefined;
  let value = points[0]![1];
  for (const [t, v] of points) {
    if (t > ts) break;
    value = v;
  }
  return value;
}

/**
 * Change since `t0`: in percent of `capital` (when given) or in currency.
 * A point is inserted at `t0` so every line starts exactly at 0 there.
 */
export function rebase(points: Point[], t0: number, capital?: number): Point[] {
  const base = valueAt(points, t0);
  if (base === undefined) return [];
  const scale = (v: number) => (capital ? ((v - base) / capital) * 100 : v - base);
  const res = points.filter(([t]) => t !== t0).map(([t, v]) => [t, scale(v)] as Point);
  res.push([t0, 0]);
  return res.sort((a, b) => a[0] - b[0]);
}

function forwardFilled(ref: MarketReference): number[][] {
  const last: number[] = [];
  return ref.data.map((row) =>
    row.map((v, i) => {
      if (v !== null && Number.isFinite(v)) last[i] = v;
      return last[i] ?? NaN;
    }),
  );
}

/**
 * Reference lines in percent since the first candle at or after `t0`:
 * an equal-start-weight basket of all members with a price there (weights drift, no costs),
 * and BTC alone.
 */
export function referenceSeries(
  ref: MarketReference,
  t0: number,
): { basket: Point[]; btc: Point[]; members: number } {
  const rows = forwardFilled(ref);
  if (rows.length === 0) return { basket: [], btc: [], members: 0 };
  const startIdx = Math.max(
    0,
    rows.findIndex((r) => r[0]! >= t0),
  );
  const start = rows[startIdx]!;
  const cols = ref.pairs.map((_, i) => i + 1).filter((c) => Number.isFinite(start[c]!));
  const btcCol = ref.pairs.findIndex((p) => p.startsWith('BTC/')) + 1;
  const basket: Point[] = [];
  const btc: Point[] = [];
  rows.forEach((r) => {
    if (cols.length) {
      const avg = cols.reduce((s, c) => s + r[c]! / start[c]!, 0) / cols.length;
      basket.push([r[0]!, (avg - 1) * 100]);
    }
    if (btcCol > 0 && Number.isFinite(start[btcCol]!)) {
      btc.push([r[0]!, (r[btcCol]! / start[btcCol]! - 1) * 100]);
    }
  });
  return { basket, btc, members: cols.length };
}

export type MarketDirection = 'up' | 'down' | 'sideways';

export interface MarketStats {
  asOf: number;
  btc24h?: number;
  basket24h?: number;
  rising: number;
  members: number;
  /** Spread of the last 24 hourly basket returns, scaled to one day */
  vol24h?: number;
}

/** Last 24h figures of the reference, as fractions (0.01 = 1%). */
export function marketStats(ref: MarketReference): MarketStats | undefined {
  const rows = forwardFilled(ref);
  const last = rows[rows.length - 1];
  if (!last) return undefined;
  const asOf = last[0]!;
  const prevIdx = rows.findIndex((r) => r[0]! >= asOf - 24 * HOUR);
  const prev = rows[prevIdx]!;
  const cols = ref.pairs
    .map((_, i) => i + 1)
    .filter((c) => Number.isFinite(last[c]!) && Number.isFinite(prev[c]!));
  const change = (c: number) => last[c]! / prev[c]! - 1;
  const btcCol = ref.pairs.findIndex((p) => p.startsWith('BTC/')) + 1;

  const returns: number[] = [];
  for (let i = Math.max(prevIdx, 1); i < rows.length; i++) {
    const r = rows[i]!;
    const p = rows[i - 1]!;
    const valid = cols.filter((c) => Number.isFinite(p[c]!) && p[c]! > 0);
    if (valid.length) {
      returns.push(valid.reduce((s, c) => s + r[c]! / p[c]!, 0) / valid.length - 1);
    }
  }
  let vol24h: number | undefined;
  if (returns.length > 1) {
    const mean = returns.reduce((s, x) => s + x, 0) / returns.length;
    const variance = returns.reduce((s, x) => s + (x - mean) ** 2, 0) / (returns.length - 1);
    vol24h = Math.sqrt(variance) * Math.sqrt(24);
  }

  return {
    asOf,
    btc24h: btcCol > 0 && cols.includes(btcCol) ? change(btcCol) : undefined,
    basket24h: cols.length ? cols.reduce((s, c) => s + change(c), 0) / cols.length : undefined,
    rising: cols.filter((c) => change(c) > 0).length,
    members: cols.length,
    vol24h,
  };
}

/** Up from +1% over 24h, down from -1%, sideways in between. */
export function marketDirection(change24h: number | undefined): MarketDirection | undefined {
  if (change24h === undefined) return undefined;
  if (change24h >= 0.01) return 'up';
  if (change24h <= -0.01) return 'down';
  return 'sideways';
}
