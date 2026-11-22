import { describe, expect, it } from 'vitest';
import { formatCandleTooltip, formatTooltipValue } from '@/utils/charts/candleTooltip';

// columns: 0 date, 1 open, 2 high, 3 low, 4 close, 5 volume, 6 rsi_4h, 7 mfi_4h,
//          8 _enter_short_signal_close, 9 enter_tag, 10 ema_fast
const row = [
  0,
  1.15,
  1.17,
  1.14,
  1.159,
  123456.789,
  12.3456789,
  null,
  1.159,
  'heisenberg|rsi2_lt20|bull',
  null,
];
const series = [
  { name: 'Candles', type: 'candlestick', encode: { y: [1, 4, 3, 2] } },
  { name: 'Volume', type: 'bar', xAxisIndex: 1, itemStyle: { color: '#777777' }, encode: { y: 5 } },
  {
    name: 'Entry',
    type: 'scatter',
    xAxisIndex: 0,
    itemStyle: { color: '#ff0000' },
    encode: { y: 8 },
    __tipLabel: 'Short entry',
    __tipTagCol: 9,
  },
  {
    name: 'ema_fast',
    type: 'line',
    xAxisIndex: 0,
    itemStyle: { color: '#4f8df7' },
    encode: { y: 10 },
  },
  {
    name: 'rsi_4h',
    type: 'line',
    xAxisIndex: 2,
    itemStyle: { color: '#4f8df7' },
    encode: { y: 6 },
  },
  {
    name: 'mfi_4h',
    type: 'line',
    xAxisIndex: 2,
    itemStyle: { color: '#f5a623' },
    encode: { y: 7 },
  },
  { name: 'Trades', type: 'scatter', xAxisIndex: 0, encode: { y: 1 } },
];
const ctx = {
  series,
  row,
  header: '2026-11-22 04:00',
  cols: { open: 1, high: 2, low: 3, close: 4 },
  paneNames: { 2: 'heisenberg RSI2 / MFI 4h' },
  candleColor: '#26a69a',
};

/** [colour, name, value] per table row, or ['pane', title]. */
function rows(html: string): string[][] {
  const doc = new DOMParser().parseFromString(html, 'text/html');
  return [...doc.querySelectorAll('tr')].map((tr) => {
    const tds = tr.querySelectorAll('td');
    if (tds.length === 1) return ['pane', tds[0]!.textContent ?? ''];
    const dot = tr.querySelector('span') as HTMLElement | null;
    return [dot?.style.background ?? '', tds[0]!.textContent ?? '', tds[1]!.textContent ?? ''];
  });
}

describe('candle tooltip', () => {
  it('lists values per pane with series colours, skipping empty values and trades', () => {
    const html = formatCandleTooltip(ctx);
    expect(html).toContain('2026-11-22 04:00');
    expect(rows(html)).toEqual([
      ['#26a69a', 'Candles', 'O 1.15  H 1.17  L 1.14  C 1.159'],
      ['#777777', 'Volume', '123457'],
      ['#ff0000', 'Short entry', 'heisenberg|rsi2_lt20|bull'],
      ['pane', 'heisenberg RSI2 / MFI 4h'],
      ['#4f8df7', 'rsi_4h', '12.3457'],
    ]);
  });

  it('escapes html and survives a missing row', () => {
    const evil = [...row];
    evil[9] = '<b>x</b>';
    expect(formatCandleTooltip({ ...ctx, row: evil })).toContain('&lt;b&gt;x&lt;/b&gt;');
    expect(formatCandleTooltip({ ...ctx, row: undefined })).not.toContain('<table');
  });

  it('formats numbers compactly', () => {
    expect(formatTooltipValue(0.000123456789)).toBe('0.000123457');
    expect(formatTooltipValue(1234.5678)).toBe('1234.57');
    expect(formatTooltipValue(Number.NaN)).toBe('');
  });
});
