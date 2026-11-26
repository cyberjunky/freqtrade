import { describe, it, expect } from 'vitest';
import type { ClosedTrade, MarketReference, WalletHistory } from '@/types';
import {
  closedPoints,
  equityPoints,
  marketDirection,
  marketStats,
  rebase,
  referenceSeries,
  valueAt,
} from '@/utils/charts/botCompare';

const H = 3_600_000;

describe('botCompare.ts', () => {
  it('reads hourly equity from the wallet history', () => {
    const history: WalletHistory = {
      columns: ['date', '__date_ts', 'total_quote'],
      length: 2,
      data: [
        ['2024-01-01T01:00:00', 2 * H, 1010],
        ['2024-01-01T00:00:00', H, 1000],
      ],
    };
    expect(equityPoints(history)).toEqual([
      [H, 1000],
      [2 * H, 1010],
    ]);
  });

  it('builds the closed-trade curve', () => {
    const trades = [
      { close_timestamp: 3 * H, profit_abs: -5 },
      { close_timestamp: 2 * H, profit_abs: 10 },
    ] as ClosedTrade[];
    expect(closedPoints(trades, H, 1000)).toEqual([
      [H, 1000],
      [2 * H, 1010],
      [3 * H, 1005],
    ]);
  });

  it('rebases to zero at t0, in percent of capital or in currency', () => {
    const pts: [number, number][] = [
      [0, 1000],
      [2 * H, 1020],
      [4 * H, 1050],
    ];
    expect(valueAt(pts, 3 * H)).toBe(1020);
    expect(valueAt(pts, -H)).toBe(1000);
    expect(rebase(pts, 3 * H, 1000)).toEqual([
      [0, -2],
      [2 * H, 0],
      [3 * H, 0],
      [4 * H, 3],
    ]);
    expect(rebase(pts, 2 * H)).toEqual([
      [0, -20],
      [2 * H, 0],
      [4 * H, 30],
    ]);
  });

  const ref: MarketReference = {
    exchange: 'blofin',
    timeframe: '1h',
    pairs: ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'SOL/USDT:USDT'],
    data: Array.from({ length: 26 }, (_, i) => [
      i * H,
      100 + i, // BTC rising
      200 - i, // ETH falling
      i < 2 ? null : 50, // SOL listed later, flat
    ]),
  };

  it('builds the basket and BTC lines from the first candle at t0', () => {
    const { basket, btc, members } = referenceSeries(ref, 0);
    expect(members).toBe(2); // SOL has no price at the start
    expect(btc[0]).toEqual([0, 0]);
    expect(btc[25]![1]).toBeCloseTo(25);
    expect(basket[25]![1]).toBeCloseTo(((125 / 100 + 175 / 200) / 2 - 1) * 100);

    const later = referenceSeries(ref, 5 * H + 1);
    expect(later.members).toBe(3);
    expect(later.btc.find(([t]) => t === 6 * H)![1]).toBe(0);
  });

  it('computes the 24h market figures', () => {
    const stats = marketStats(ref)!;
    expect(stats.asOf).toBe(25 * H);
    expect(stats.btc24h).toBeCloseTo(125 / 101 - 1);
    expect(stats.members).toBe(2); // SOL had no price 24h ago
    expect(stats.rising).toBe(1);
    expect(stats.basket24h).toBeCloseTo((125 / 101 + 175 / 199) / 2 - 1);
    expect(stats.vol24h).toBeGreaterThan(0);
  });

  it('labels the direction at +-1%', () => {
    expect(marketDirection(0.01)).toBe('up');
    expect(marketDirection(-0.012)).toBe('down');
    expect(marketDirection(0.004)).toBe('sideways');
    expect(marketDirection(undefined)).toBeUndefined();
  });
});
