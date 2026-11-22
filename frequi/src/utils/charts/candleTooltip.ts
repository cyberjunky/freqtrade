/**
 * HTML tooltip of the candle chart: every series at the hovered candle (not only the pane under
 * the mouse), grouped per pane with the subplot name as a small title, each row with a dot in the
 * colour of its line. Rows without a value at that candle are left out.
 *
 * HTML, not richText: in richText mode ECharts only uses the styles it creates itself (markers),
 * so custom colours and column widths from `textStyle.rich` are silently ignored.
 */

export interface TooltipSeries {
  name?: string;
  type?: string;
  xAxisIndex?: number;
  encode?: { y?: number | number[] };
  tooltip?: { show?: boolean };
  itemStyle?: { color?: unknown };
  lineStyle?: { color?: unknown };
  /** Signal series (Entry / Exit): the label to show, e.g. "Short entry". */
  __tipLabel?: string;
  /** Signal series: column of the tag shown as its value. */
  __tipTagCol?: number;
}

export interface CandleTooltipContext {
  series: TooltipSeries[];
  row: unknown[] | undefined;
  header: string;
  cols: { open: number; high: number; low: number; close: number };
  /** Pane (grid / xAxis index) -> subplot name. Panes 0 (candles) and 1 (volume) have none. */
  paneNames: Record<number, string>;
  /** Dot colour of the candles. */
  candleColor: string;
}

const MUTED = '#9ba5b3';

export function escapeHtml(value: unknown): string {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export function formatTooltipValue(value: unknown): string {
  if (typeof value === 'number') {
    if (!Number.isFinite(value)) return '';
    const abs = Math.abs(value);
    if (abs >= 100000) return value.toFixed(0);
    if (abs >= 1000) return value.toFixed(2);
    return String(Number(value.toPrecision(6)));
  }
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  return String(value);
}

function hasValue(value: unknown): boolean {
  if (value === null || value === undefined || value === '') return false;
  return !(typeof value === 'number' && !Number.isFinite(value));
}

export function seriesColor(s: TooltipSeries, fallback = MUTED): string {
  const c = s?.itemStyle?.color ?? s?.lineStyle?.color;
  return typeof c === 'string' && c ? c : fallback;
}

function rowHtml(color: string, name: string, value: string): string {
  const dot =
    `<span style="display:inline-block;width:8px;height:8px;border-radius:50%;` +
    `margin-right:6px;background:${escapeHtml(color)}"></span>`;
  return (
    `<tr><td style="padding:1px 12px 1px 0;white-space:nowrap">${dot}${escapeHtml(name)}</td>` +
    `<td style="padding:1px 0;font-family:'IBM Plex Mono',monospace;white-space:nowrap">` +
    `${escapeHtml(value)}</td></tr>`
  );
}

function paneHtml(title: string): string {
  return (
    `<tr><td colspan="2" style="padding:6px 0 1px;color:${MUTED};font-size:11px">` +
    `${escapeHtml(title)}</td></tr>`
  );
}

export function formatCandleTooltip(ctx: CandleTooltipContext): string {
  const { series, row, header, cols, paneNames, candleColor } = ctx;
  const head = header
    ? `<div style="font-weight:600;margin-bottom:4px">${escapeHtml(header)}</div>`
    : '';
  if (!row) return head;

  const panes = new Map<number, string[]>();
  const seen = new Set<string>();
  for (const s of series) {
    if (!s?.name || s.tooltip?.show === false || s.name === 'Trades') continue;
    // Volume (pane 1) sits right under the candles, so list it with them.
    const pane = (s.xAxisIndex ?? 0) === 1 ? 0 : (s.xAxisIndex ?? 0);
    let line: string;
    if (s.type === 'candlestick') {
      const [o, h, l, c] = [row[cols.open], row[cols.high], row[cols.low], row[cols.close]];
      if (!hasValue(o)) continue;
      const f = formatTooltipValue;
      line = rowHtml(candleColor, s.name, `O ${f(o)}  H ${f(h)}  L ${f(l)}  C ${f(c)}`);
    } else {
      const y = Array.isArray(s.encode?.y) ? s.encode.y[0] : s.encode?.y;
      if (y === undefined || y < 0) continue;
      const value = row[y];
      if (!hasValue(value)) continue;
      if (s.__tipLabel) {
        const tag = s.__tipTagCol !== undefined && s.__tipTagCol >= 0 ? row[s.__tipTagCol] : null;
        line = rowHtml(
          seriesColor(s),
          s.__tipLabel,
          formatTooltipValue(hasValue(tag) ? tag : value),
        );
      } else {
        if (seen.has(s.name)) continue;
        seen.add(s.name);
        line = rowHtml(seriesColor(s), s.name, formatTooltipValue(value));
      }
    }
    if (!panes.has(pane)) panes.set(pane, []);
    panes.get(pane)!.push(line);
  }

  const body: string[] = [];
  [...panes.keys()]
    .sort((a, b) => a - b)
    .forEach((pane) => {
      const title = paneNames[pane];
      if (pane > 1 && title) body.push(paneHtml(title));
      body.push(...panes.get(pane)!);
    });
  return `${head}<table style="border-collapse:collapse">${body.join('')}</table>`;
}
