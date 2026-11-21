import Favico from 'favico.js';

/**
 * Keeps the document title and the favicon badge in sync with the open trade
 * count of the active bot (setting "Show open trades in header").
 */
export function useTitleAndFavicon() {
  const botStore = useBotStore();
  const settingsStore = useSettingsStore();
  let favicon: Favico | undefined;

  const openTradeCount = computed(() => botStore.activeBotorUndefined?.openTradeCount ?? 0);

  function setPill(tradeCount: number) {
    try {
      if (!favicon) {
        favicon = new Favico({ animation: 'none' });
      }
      if (tradeCount !== 0 && settingsStore.openTradesInTitle === OpenTradeVizOptions.showPill) {
        favicon.badge(tradeCount);
      } else {
        favicon.reset();
      }
    } catch (error) {
      console.warn('Favicon badge not available', error);
    }
  }

  function setTitle() {
    let title = 'FreqUI';
    if (settingsStore.openTradesInTitle === OpenTradeVizOptions.asTitle) {
      title = `(${openTradeCount.value}) ${title}`;
    }
    const name = botStore.activeBotorUndefined?.uiBotName;
    if (name) {
      title = `${title} - ${name}`;
    }
    document.title = title;
  }

  watch(
    [
      openTradeCount,
      () => settingsStore.openTradesInTitle,
      () => botStore.activeBotorUndefined?.uiBotName,
    ],
    () => {
      setTitle();
      setPill(openTradeCount.value);
    },
  );
  onMounted(() => setTitle());
}
