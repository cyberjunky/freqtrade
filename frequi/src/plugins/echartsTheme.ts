import { registerTheme } from 'echarts/core';
import type { ThemeKind, ThemeTokens } from '@/utils/themeTokens';
import { readThemeTokens } from '@/utils/themeTokens';

/**
 * Build an ECharts theme from the design tokens.
 * Registered under the names `dark` and `light` - the names all charts already
 * pass via `:theme="settingsStore.chartTheme"` - so every chart re-themes on toggle.
 */
function buildTheme(t: ThemeTokens) {
  const axis = {
    axisLine: { show: true, lineStyle: { color: t.border } },
    axisTick: { show: false, lineStyle: { color: t.border } },
    axisLabel: { color: t.muted, fontFamily: t['font-mono'], fontSize: 11 },
    nameTextStyle: { color: t['text-2'], fontFamily: t['font-sans'], fontSize: 11 },
    splitLine: { show: true, lineStyle: { color: t.grid } },
    splitArea: { show: false },
    axisPointer: {
      lineStyle: { color: t.idle },
      label: {
        backgroundColor: t.border,
        color: t.text,
        fontFamily: t['font-mono'],
        fontSize: 11,
      },
    },
  };
  return {
    color: t.series,
    backgroundColor: 'transparent',
    textStyle: { fontFamily: t['font-sans'], color: t['text-2'] },
    title: {
      textStyle: { color: t['text-2'], fontSize: 12, fontWeight: 600 },
      subtextStyle: { color: t.muted },
    },
    legend: {
      textStyle: { color: t['text-2'], fontSize: 11 },
      inactiveColor: t.idle,
      itemWidth: 14,
      itemHeight: 8,
      pageTextStyle: { color: t['text-2'] },
      pageIconColor: t['text-2'],
      pageIconInactiveColor: t.idle,
    },
    tooltip: {
      backgroundColor: t.panel,
      borderColor: t.border,
      borderWidth: 1,
      padding: [8, 10],
      textStyle: { color: t.text, fontSize: 12, fontFamily: t['font-sans'] },
      axisPointer: {
        lineStyle: { color: t.idle },
        crossStyle: { color: t.idle },
        label: { backgroundColor: t.border, color: t.text },
      },
    },
    axisPointer: {
      lineStyle: { color: t.idle },
      label: { backgroundColor: t.border, color: t.text },
    },
    categoryAxis: axis,
    valueAxis: axis,
    timeAxis: axis,
    logAxis: axis,
    line: { lineStyle: { width: 2 }, symbolSize: 4, symbol: 'circle', smooth: false },
    bar: { itemStyle: { borderRadius: 0 } },
    pie: {
      itemStyle: { borderColor: t.panel, borderWidth: 2 },
      label: { color: t['text-2'], fontSize: 11 },
      labelLine: { lineStyle: { color: t.idle } },
    },
    candlestick: {
      itemStyle: { color: t.pos, color0: t.neg, borderColor: t.pos, borderColor0: t.neg },
    },
    dataZoom: {
      backgroundColor: 'transparent',
      borderColor: t.border,
      fillerColor: t['series-wash'],
      dataBackgroundColor: t.grid,
      handleColor: t.idle,
      handleStyle: { color: t.idle, borderColor: t.idle },
      moveHandleStyle: { color: t.idle },
      textStyle: { color: t.muted, fontFamily: t['font-mono'], fontSize: 10 },
      dataBackground: {
        lineStyle: { color: t.idle },
        areaStyle: { color: t.grid },
      },
      selectedDataBackground: {
        lineStyle: { color: t['series-1'] },
        areaStyle: { color: t['series-wash'] },
      },
      brushStyle: { color: t['series-wash'] },
    },
    visualMap: { textStyle: { color: t['text-2'] } },
    markLine: {
      lineStyle: { color: t.idle },
      label: { color: t['text-2'], fontSize: 10 },
    },
    markPoint: { label: { color: t.text } },
    toolbox: { iconStyle: { borderColor: t.muted } },
  };
}

export function registerFtEchartsThemes() {
  (['dark', 'light'] as ThemeKind[]).forEach((kind) => {
    registerTheme(kind, buildTheme(readThemeTokens(kind)));
  });
}
