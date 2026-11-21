<script setup lang="ts">
import type Popover from 'primevue/popover';

const newblacklistpair = ref('');
const blackListShow = ref(false);
const blacklistAddPopover = ref<InstanceType<typeof Popover>>();
const blacklistSelect = ref<number[]>([]);
const botStore = useBotStore();

function initBlacklist() {
  if (botStore.activeBot.whitelist.length === 0) {
    botStore.activeBot.getWhitelist();
  }
  if (botStore.activeBot.blacklist.length === 0) {
    botStore.activeBot.getBlacklist();
  }
}

function addBlacklistPair() {
  if (newblacklistpair.value) {
    blackListShow.value = false;
    blacklistAddPopover.value?.hide();

    botStore.activeBot.addBlacklist({ blacklist: [newblacklistpair.value] });
    newblacklistpair.value = '';
  }
}

function showPopover(event: MouseEvent) {
  blacklistAddPopover.value?.show(event);
}

function blacklistSelectClick(key: number) {
  const index = blacklistSelect.value.indexOf(key);
  if (index > -1) {
    blacklistSelect.value.splice(index, 1);
  } else {
    blacklistSelect.value.push(key);
  }
}

function deletePairs() {
  if (blacklistSelect.value.length === 0) {
    console.log('nothing to delete');
    return;
  }
  // const pairlist = blacklistSelect.value;
  const pairlist = botStore.activeBot.blacklist.filter(
    (value, index) => blacklistSelect.value.indexOf(index) > -1,
  );
  console.log('Deleting pairs: ', pairlist);
  botStore.activeBot.deleteBlacklist(pairlist);
  blacklistSelect.value = [];
}
onMounted(() => {
  initBlacklist();
});
</script>

<template>
  <div class="ft-stack">
    <div v-if="botStore.activeBot.pairlistMethods.length">
      <h3 class="ft-label">Pairlist methods</h3>
      <ul class="ft-chiplist">
        <li v-for="(method, key) in botStore.activeBot.pairlistMethods" :key="key" class="ft-chip">
          {{ method }}
        </li>
      </ul>
    </div>

    <div>
      <h3 class="ft-label">
        Whitelist
        <span class="ft-dim ft-mono">({{ botStore.activeBot.whitelist.length }})</span>
      </h3>
      <ul v-if="botStore.activeBot.whitelist.length" class="ft-chiplist">
        <li
          v-for="(pair, key) in botStore.activeBot.whitelist"
          :key="key"
          :aria-label="pair"
          class="ft-chip"
        >
          {{ pair }}
        </li>
      </ul>
      <p v-else class="ft-hint">
        Whitelist unavailable. Please log in and make sure the bot is running.
      </p>
    </div>

    <div>
      <div class="ft-bl-head">
        <h3
          class="ft-label"
          title="Blacklist - select pairs, then use 'Remove selected' to remove them"
        >
          Blacklist
          <span class="ft-dim ft-mono">({{ botStore.activeBot.blacklist.length }})</span>
        </h3>
        <div class="ft-bl-actions">
          <Button size="small" severity="secondary" label="Add pair" @click="showPopover">
            <template #icon><i-mdi-plus /></template>
          </Button>
          <Button
            v-if="botStore.activeBot.botFeatures.botBlacklistModify"
            size="small"
            severity="danger"
            :label="`Remove selected${blacklistSelect.length ? ` (${blacklistSelect.length})` : ''}`"
            title="Select pairs below to remove them from the blacklist."
            :disabled="blacklistSelect.length === 0"
            @click="deletePairs"
          >
            <template #icon><i-mdi-delete /></template>
          </Button>
        </div>
      </div>
      <Popover ref="blacklistAddPopover">
        <form class="ft-bl-form" @submit.prevent="addBlacklistPair">
          <label for="pair-input" class="ft-label">Add pair to blacklist</label>
          <div class="flex gap-2">
            <InputText
              id="pair-input"
              v-model="newblacklistpair"
              required
              autofocus
              size="small"
              placeholder="e.g. DOGE/USDT or .*DOWN/.*"
            ></InputText>
            <Button
              id="blacklist-submit"
              size="small"
              severity="primary"
              type="submit"
              label="Add"
            />
          </div>
        </form>
      </Popover>
      <ul v-if="botStore.activeBot.blacklist.length" class="ft-chiplist">
        <li v-for="(pair, key) in botStore.activeBot.blacklist" :key="key">
          <button
            type="button"
            class="ft-chip"
            :class="{ 'is-selected': blacklistSelect.indexOf(key) > -1 }"
            :aria-pressed="blacklistSelect.indexOf(key) > -1"
            :title="pair"
            @click="blacklistSelectClick(key)"
          >
            <i-mdi-check v-if="blacklistSelect.indexOf(key) > -1" aria-hidden="true" />{{ pair }}
          </button>
        </li>
      </ul>
      <p v-else class="ft-hint">Blacklist is empty.</p>
    </div>
  </div>
</template>

<style scoped>
.ft-bl-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 6px;
}
.ft-bl-head .ft-label {
  margin: 0;
}
.ft-bl-actions {
  display: flex;
  gap: 6px;
}
.ft-bl-form {
  min-width: 260px;
}
</style>
