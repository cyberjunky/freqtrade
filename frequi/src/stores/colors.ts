const STORE_UI_COLORS = 'ftUIColorSettings';

export enum ColorPreferences {
  GREEN_UP = 'greenUp',
  RED_UP = 'redUp',
}

/**
 * Chart colours. The values come from the design tokens (theme aware),
 * only the up/down preference is a user setting.
 */
export const useColorStore = defineStore(
  'colorStore',
  () => {
    const colorPreference = ref<ColorPreferences>(ColorPreferences.GREEN_UP);

    const colorProfit = computed(() => themeTokens.pos);
    const colorLoss = computed(() => themeTokens.neg);
    const colorUp = computed(() =>
      colorPreference.value === ColorPreferences.GREEN_UP ? themeTokens.pos : themeTokens.neg,
    );
    const colorDown = computed(() =>
      colorPreference.value === ColorPreferences.GREEN_UP ? themeTokens.neg : themeTokens.pos,
    );

    /** Kept for API compatibility - colours are derived reactively now. */
    function updateProfitLossColor() {
      // no-op
    }

    return { colorPreference, colorProfit, colorLoss, colorUp, colorDown, updateProfitLossColor };
  },
  {
    persist: {
      key: STORE_UI_COLORS,
      pick: ['colorPreference'],
    },
  },
);

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useColorStore, import.meta.hot));
}
