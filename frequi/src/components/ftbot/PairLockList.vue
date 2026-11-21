<script setup lang="ts">
import type { Lock } from '@/types';

const botStore = useBotStore();

function removePairLock(item: Lock) {
  console.log(item);
  if (item.id !== undefined) {
    botStore.activeBot.deleteLock(item.id);
  } else {
    showAlert('This Freqtrade version does not support deleting locks.');
  }
}
</script>

<template>
  <DataTable size="small" :value="botStore.activeBot.activeLocks" scrollable>
    <template #empty>No active pair locks.</template>
    <Column field="pair" header="Pair" class="ft-mono"></Column>
    <Column field="lock_end_timestamp" header="Until" class="ft-num">
      <template #body="{ data, field }">
        {{ timestampms(data[field as string]) }}
      </template>
    </Column>
    <Column field="side" header="Side"></Column>
    <Column field="reason" header="Reason"></Column>
    <Column field="actions" header="" class="ft-num">
      <template #body="{ data }">
        <Button
          size="small"
          severity="secondary"
          label="Unlock"
          title="Delete lock"
          @click="removePairLock(data as Lock)"
        >
          <template #icon><i-mdi-lock-open-variant-outline /></template>
        </Button>
      </template>
    </Column>
  </DataTable>
</template>
