<script setup lang="ts">
/**
 * Confirmation dialog. Destructive / trading actions go through this before executing.
 */
export interface MsgBoxObject {
  title: string;
  message: string;
  accept: () => void;
  /** Label of the confirming button (defaults to "Confirm") */
  confirmLabel?: string;
  /** Destructive action: confirm button is rendered danger-solid */
  danger?: boolean;
  /** Additional warning line (e.g. LIVE - real money) */
  warning?: string;
}
const showRef = ref<boolean>(false);
const title = ref<string>('');
const message = ref<string>('');
const confirmLabel = ref<string>('Confirm');
const danger = ref<boolean>(false);
const warning = ref<string>('');
const accept = ref<() => void>(() => {
  console.warn('Accepted not set.');
});

const msgBoxOK = () => {
  accept.value();
  showRef.value = false;
};

function show(msg: MsgBoxObject) {
  title.value = msg.title;
  message.value = msg.message;
  confirmLabel.value = msg.confirmLabel ?? 'Confirm';
  danger.value = msg.danger ?? false;
  warning.value = msg.warning ?? '';
  showRef.value = true;
  accept.value = msg.accept;
}

defineExpose({ show });
</script>

<template>
  <Dialog
    id="MsgBoxModal"
    v-model:visible="showRef"
    modal
    :header="title"
    :draggable="false"
    :style="{ width: '440px' }"
  >
    <p class="ft-confirm-msg">{{ message }}</p>
    <p v-if="warning" class="ft-confirm-warn"><i-mdi-alert aria-hidden="true" /> {{ warning }}</p>
    <template #footer>
      <Button label="Cancel" severity="secondary" autofocus @click="showRef = false" />
      <Button
        :label="confirmLabel"
        :severity="danger ? 'danger' : 'primary'"
        :class="{ 'ft-danger-solid': danger }"
        @click="msgBoxOK"
      />
    </template>
  </Dialog>
</template>

<style scoped>
.ft-confirm-msg {
  margin: 0;
  color: var(--ft-text);
  white-space: pre-line;
}
.ft-confirm-warn {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 10px 0 0;
  color: var(--ft-warning);
  font-weight: 600;
  font-size: 12px;
}
</style>
