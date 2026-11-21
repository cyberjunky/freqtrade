<script setup lang="ts">
import type { MsgBoxObject } from '@/components/general/MessageBox.vue';
import MessageBox from '@/components/general/MessageBox.vue';

import type { BacktestHistoryEntry } from '@/types';
import InfoBox from '../general/InfoBox.vue';

const botStore = useBotStore();
const msgBox = ref<typeof MessageBox>();
const filterText = ref('');
const filterTextDebounced = refDebounced(filterText, 350, { maxWait: 1000 });

onMounted(() => {
  botStore.activeBot.getBacktestHistory();
});

function deleteBacktestResult(result: BacktestHistoryEntry) {
  const msg: MsgBoxObject = {
    title: 'Delete result',
    message: `Delete result ${result.filename} from disk?`,
    accept: () => {
      botStore.activeBot.deleteBacktestHistoryResult(result);
    },
  };
  msgBox.value?.show(msg);
}

const filteredList = computed(() =>
  botStore.activeBot.backtestHistoryList.filter(
    (r) =>
      r.filename.toLowerCase().includes(filterTextDebounced.value.toLowerCase()) ||
      r.strategy.toLowerCase().includes(filterTextDebounced.value.toLowerCase()),
  ),
);
function rowClick(row) {
  botStore.activeBot.getBacktestHistoryResult(row.data);
}
</script>

<template>
  <div>
    <div class="flex flex-wrap items-center gap-3 px-3 py-2 border-b border-line">
      <span class="ft-hint grow"
        >Load stored results from disk. Click several rows to load all of them.</span
      >
      <Button
        title="Refresh"
        aria-label="Refresh"
        size="small"
        severity="secondary"
        @click="botStore.activeBot.getBacktestHistory"
        ><template #icon><i-mdi-refresh /></template
      ></Button>
      <InputText
        id="trade-filter"
        v-model="filterText"
        type="text"
        size="small"
        placeholder="Filter results"
        title="Filter results"
        aria-label="Filter results"
      />
    </div>
    <DataTable
      v-if="botStore.activeBot.backtestHistoryList.length > 0"
      size="small"
      scrollable
      scroll-height="50rem"
      :virtual-scroller-options="{ itemSize: 46 }"
      :value="filteredList"
      @row-click="rowClick"
    >
      <Column field="strategy" header="Strategy"></Column>
      <Column field="timeframe" header="Details">
        <template #body="{ data }">
          <strong>{{ data.timeframe }}</strong>
          <span v-if="data.backtest_start_ts && data.backtest_end_ts" class="ms-1">
            {{ timestampToTimeRangeString(data.backtest_start_ts * 1000) }}-{{
              timestampToTimeRangeString(data.backtest_end_ts * 1000)
            }}</span
          >
        </template>
      </Column>
      <Column field="backtest_start_time" header="Backtest Time">
        <template #body="{ data }">
          <DateTimeTZ :date="data.backtest_start_time * 1000" />
        </template>
      </Column>
      <Column field="filename" header="Filename"></Column>
      <Column field="actions" header="Actions">
        <template #body="{ data }">
          <div class="flex items-center">
            <InfoBox
              v-if="botStore.activeBot.botFeatures.backtestSetNotes"
              :class="data.notes ? 'opacity-100' : 'opacity-0'"
              :hint="data.notes ?? ''"
            ></InfoBox>
            <Button
              v-if="botStore.activeBot.botFeatures.backtestDelete"
              class="ms-1"
              size="small"
              title="Load this Result."
              :disabled="data.run_id in botStore.activeBot.backtestHistory"
              @click.stop="botStore.activeBot.getBacktestHistoryResult(data)"
            >
              <template #icon>
                <i-mdi-arrow-right />
              </template>
            </Button>
            <Button
              v-if="botStore.activeBot.botFeatures.backtestDelete"
              class="ms-1"
              size="small"
              severity="secondary"
              title="Delete this Result."
              :disabled="data.run_id in botStore.activeBot.backtestHistory"
              @click.stop="deleteBacktestResult(data)"
            >
              <template #icon>
                <i-mdi-delete />
              </template>
            </Button>
          </div>
        </template>
      </Column>
    </DataTable>
  </div>
  <MessageBox ref="msgBox" />
</template>
