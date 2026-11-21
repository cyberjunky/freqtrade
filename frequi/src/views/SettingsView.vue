<script setup lang="ts">
import { FtWsMessageTypes } from '@/types/wsMessageTypes';
import type { SegmentedItem } from '@/components/ui/FtSegmented.vue';
import type { ThemeMode } from '@/composables/theme';

const settingsStore = useSettingsStore();
const colorStore = useColorStore();
const botStore = useBotStore();
const { mode: themeMode } = useThemeMode();

const themeItems: SegmentedItem<ThemeMode>[] = THEME_MODES.map((m) => ({
  value: m.value,
  label: m.label,
}));

const timezoneOptions = ['UTC', Intl.DateTimeFormat().resolvedOptions().timeZone];
const openTradesOptions = [
  { value: OpenTradeVizOptions.showPill, text: 'Show pill in icon' },
  { value: OpenTradeVizOptions.asTitle, text: 'Show in title' },
  { value: OpenTradeVizOptions.noOpenTrades, text: "Don't show open trades in header" },
];
const colorPreferenceOptions = [
  { value: ColorPreferences.GREEN_UP, text: 'Green up / red down' },
  { value: ColorPreferences.RED_UP, text: 'Green down / red up' },
];
const labelSideItems: SegmentedItem<'left' | 'right'>[] = [
  { value: 'left', label: 'Left' },
  { value: 'right', label: 'Right' },
];
</script>

<template>
  <div class="ft-container ft-stack ft-settings">
    <div>
      <h1 class="ft-page-title">FreqUI Settings</h1>
      <p class="ft-hint ft-mono">UI version {{ settingsStore.uiVersion }}</p>
    </div>

    <FtPanel title="Bots">
      <p class="ft-hint mb-3">
        Bots connected in this browser. Drag to change the order of the tabs, rename, re-login or
        remove a bot.
      </p>
      <BotList />
    </FtPanel>

    <div class="ft-grid-2">
      <FtPanel title="Interface">
        <div class="ft-form">
          <div>
            <span class="ft-label">Theme</span>
            <FtSegmented v-model="themeMode" :items="themeItems" label="Theme" />
            <small class="ft-hint block mt-1">Auto follows your operating system setting.</small>
          </div>

          <div>
            <label class="ft-label" for="open-trades-select">Show open trades in header</label>
            <Select
              v-model="settingsStore.openTradesInTitle"
              label-id="open-trades-select"
              :options="openTradesOptions"
              option-label="text"
              option-value="value"
              class="w-full"
            />
            <small class="ft-hint">Decide if open trades should be visualized</small>
          </div>

          <div>
            <label class="ft-label" for="timezone-select">Timezone</label>
            <Select
              v-model="settingsStore.timezone"
              label-id="timezone-select"
              :options="timezoneOptions"
              class="w-full"
            />
            <small class="ft-hint"
              >Used for all timestamps (UTC is recommended as exchanges usually work in UTC)</small
            >
          </div>

          <BaseCheckbox v-model="botStore.globalAutoRefresh">
            Auto-refresh
            <template #hint>
              Master switch for automatic refreshing of all bots. Individual bots can be switched
              off in the bot list above.
            </template>
          </BaseCheckbox>

          <BaseCheckbox v-model="settingsStore.backgroundSync">
            Background sync
            <template #hint> Keep background sync running while other bots are selected. </template>
          </BaseCheckbox>

          <BaseCheckbox v-model="settingsStore.confirmDialog">
            Show confirm dialog for trade exits
            <template #hint
              >Use confirmation dialogs when force-exiting a trade. When disabled, a
              <strong>NO CONFIRM</strong> warning is shown in the top bar.
            </template>
          </BaseCheckbox>
        </div>
      </FtPanel>

      <FtPanel title="Charts">
        <div class="ft-form">
          <div>
            <span class="ft-label">Chart scale side</span>
            <FtSegmented
              v-model="settingsStore.chartLabelSide"
              :items="labelSideItems"
              label="Chart scale side"
            />
          </div>

          <div>
            <span class="ft-label">Candle colour preference</span>
            <div class="flex flex-wrap gap-x-5 gap-y-2 items-center">
              <div
                v-for="option in colorPreferenceOptions"
                :key="option.value"
                class="flex items-center gap-2"
              >
                <RadioButton
                  v-model="colorStore.colorPreference"
                  :value="option.value"
                  :input-id="`input-id${option.value}`"
                  size="small"
                />
                <label :for="`input-id${option.value}`" class="flex items-center">
                  <span class="mr-1">{{ option.text }}</span>
                  <i-mdi-arrow-up-thin
                    :class="option.value === ColorPreferences.GREEN_UP ? 'ft-pos' : 'ft-neg'"
                  />
                  <i-mdi-arrow-down-thin
                    :class="option.value === ColorPreferences.GREEN_UP ? 'ft-neg' : 'ft-pos'"
                    class="-ml-2"
                  />
                </label>
              </div>
            </div>
          </div>

          <BaseCheckbox v-model="settingsStore.useHeikinAshiCandles">
            Use Heikin Ashi candles
            <template #hint>Use Heikin Ashi candles in your charts</template>
          </BaseCheckbox>

          <BaseCheckbox v-model="settingsStore.useReducedPairCalls">
            Only request necessary columns
            <template #hint
              >Can reduce the transfer size for large dataframes. May require additional calls if
              the plot config changes.</template
            >
          </BaseCheckbox>

          <div>
            <label class="ft-label" for="candle-count"
              >Default number of candles to display (defaults to 250)</label
            >
            <div class="flex flex-row gap-4 w-full items-center">
              <Slider
                v-model="settingsStore.chartDefaultCandleCount"
                class="flex-1"
                :step="50"
                :min="100"
                :max="2000"
              />
              <InputNumber
                v-model="settingsStore.chartDefaultCandleCount"
                input-id="candle-count"
                :step="50"
                :min="100"
                :max="2000"
                class="ft-candlecount"
              />
            </div>
          </div>
        </div>
      </FtPanel>
    </div>

    <div class="ft-grid-2">
      <FtPanel title="Notifications">
        <div class="ft-form">
          <BaseCheckbox v-model="settingsStore.notifications[FtWsMessageTypes.entryFill]">
            Entry notifications
          </BaseCheckbox>
          <BaseCheckbox v-model="settingsStore.notifications[FtWsMessageTypes.exitFill]">
            Exit notifications
          </BaseCheckbox>
          <BaseCheckbox v-model="settingsStore.notifications[FtWsMessageTypes.entryCancel]">
            Entry cancel notifications
          </BaseCheckbox>
          <BaseCheckbox v-model="settingsStore.notifications[FtWsMessageTypes.exitCancel]">
            Exit cancel notifications
          </BaseCheckbox>
        </div>
      </FtPanel>

      <FtPanel title="Backtesting">
        <div class="ft-form">
          <div>
            <label for="backtestMetrics" class="ft-label">Backtesting metrics</label>
            <MultiSelect
              id="backtestMetrics"
              v-model="settingsStore.backtestAdditionalMetrics"
              :options="availableBacktestMetrics"
              option-label="header"
              option-value="field"
              class="w-full"
              display="chip"
            />
            <small class="ft-hint"
              >Select which metrics should be shown on a per pair / tag basis.</small
            >
          </div>
        </div>
      </FtPanel>
    </div>
  </div>
</template>

<style scoped>
.ft-settings {
  max-width: 1100px;
}
.ft-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.ft-candlecount {
  width: 96px;
}
</style>
