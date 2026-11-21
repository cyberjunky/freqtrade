<script setup lang="ts">
import type { AuthStorageWithBotId } from '@/types';

withDefaults(
  defineProps<{
    loginText?: string;
    /** Render only the dialog - it is opened through `openLoginModal()` */
    hideButton?: boolean;
  }>(),
  {
    loginText: 'Login',
    hideButton: false,
  },
);
const loginViewOpen = ref(false);
const loginInfo = ref<AuthStorageWithBotId | undefined>(undefined);

const handleLoginResult = (result: boolean) => {
  if (result) {
    loginViewOpen.value = false;
  }
};

const openLoginModal = async (botInfo: AuthStorageWithBotId | undefined = undefined) => {
  loginInfo.value = botInfo;
  await nextTick();
  loginViewOpen.value = true;
};
defineExpose({
  openLoginModal,
});
</script>

<template>
  <div :class="{ contents: hideButton }">
    <Button v-if="!hideButton" severity="primary" @click="openLoginModal()"
      ><i-mdi-login aria-hidden="true" />{{ loginText }}</Button
    >
    <Dialog
      id="modal-prevent-closing"
      v-model:visible="loginViewOpen"
      :header="loginInfo ? 'Log in again' : 'Login to your bot'"
      modal
      :draggable="false"
      :dismissable-mask="true"
      :style="{ width: '440px' }"
    >
      <BotLogin in-modal :existing-auth="loginInfo" @login-result="handleLoginResult" />
    </Dialog>
  </div>
</template>
