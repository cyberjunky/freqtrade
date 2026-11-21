<script setup lang="ts">
import type { BacktestResultInMemory, BacktestResultUpdate } from '@/types';

withDefaults(
  defineProps<{
    backtestHistory: Record<string, BacktestResultInMemory>;
    selectedBacktestResultKey?: string;
    canUseModify?: boolean;
  }>(),
  {
    selectedBacktestResultKey: '',
    canUseModify: false,
  },
);

const emit = defineEmits<{
  selectionChange: [value: string];
  removeResult: [value: string];
  updateResult: [value: BacktestResultUpdate];
}>();

const setBacktestResult = (key: string) => {
  emit('selectionChange', key);
};

function confirmInput(run_id: string, result: BacktestResultInMemory) {
  result.metadata.editing = !result.metadata.editing;
  if (result.metadata.filename) {
    emit('updateResult', {
      run_id: run_id,
      notes: result.metadata.notes ?? '',
      filename: result.metadata.filename,
      strategy: result.metadata.strategyName,
    });
  }
}
</script>

<template>
  <div class="flex flex-col items-stretch">
    <ul class="divide-y divide-solid divide-line border border-line rounded-md overflow-hidden">
      <li
        v-for="[key, result] in Object.entries(backtestHistory)"
        :key="key"
        button
        :class="{
          'bg-selected shadow-[inset_2px_0_0_var(--ft-primary)]': key === selectedBacktestResultKey,
        }"
        class="flex justify-between items-center gap-2 py-1.5 px-2 cursor-pointer hover:bg-hover"
        @click="setBacktestResult(key)"
      >
        <template v-if="!result.metadata.editing">
          <BacktestResultSelectEntry :backtest-result="result" :can-use-modify="canUseModify" />
          <div class="flex gap-1">
            <Button
              v-if="canUseModify"
              class="flex-nowrap"
              size="small"
              severity="secondary"
              title="Modify result notes."
              @click.stop="result.metadata.editing = !result.metadata.editing"
            >
              <template #icon>
                <i-mdi-pencil />
              </template>
            </Button>
            <Button
              size="small"
              class="flex-nowrap"
              severity="secondary"
              title="Delete this Result from UI."
              @click.stop="emit('removeResult', key)"
            >
              <template #icon>
                <i-mdi-delete />
              </template>
            </Button>
          </div>
        </template>
        <template v-if="result.metadata.editing">
          <Textarea v-model="result.metadata.notes" placeholder="notes" size="small"> </Textarea>

          <Button size="small" title="Confirm" @click.stop="confirmInput(key, result)">
            <template #icon>
              <i-mdi-check />
            </template>
          </Button>
        </template>
      </li>
    </ul>
  </div>
</template>
