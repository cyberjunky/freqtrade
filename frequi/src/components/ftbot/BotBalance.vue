<script setup lang="ts">
import type { BalanceValues } from '@/types';

const botStore = useBotStore();
const hideSmallBalances = ref(true);
const showBotOnly = ref(true);

const smallBalance = computed<number>(() => {
  return Number((1.1 ** botStore.activeBot.stakeCurrencyDecimals).toFixed(8));
});

const canUseBotBalance = computed(() => {
  return botStore.activeBot.botFeatures.hasBotBalance;
});

const balanceCurrencies = computed(() => {
  return botStore.activeBot.balance.currencies?.filter(
    (v) =>
      (!hideSmallBalances.value || v.est_stake >= smallBalance.value) &&
      (!canUseBotBalance.value || !showBotOnly.value || (v.is_bot_managed ?? true) === true),
  );
});

const formatCurrency = (value) => {
  return value ? formatPrice(value, botStore.activeBot.stakeCurrencyDecimals) : '';
};

const chartValues = computed<BalanceValues[]>(() => {
  return balanceCurrencies.value?.map((v) => {
    return {
      balance:
        showBotOnly.value && canUseBotBalance.value && v.bot_owned != undefined
          ? v.bot_owned
          : v.is_position === true
            ? v.position
            : v.balance,
      currency: v.currency,
      est_stake:
        showBotOnly.value && canUseBotBalance.value
          ? (v.est_stake_bot ?? v.est_stake)
          : v.est_stake,
      free: showBotOnly.value && canUseBotBalance.value ? (v.bot_owned ?? v.free) : v.free,
      used: v.used,
      stake: v.stake,
    };
  });
});

const tableFields = computed(() => {
  return [
    { field: 'currency', header: 'Currency' },
    {
      field: showBotOnly.value && canUseBotBalance.value ? 'bot_owned' : 'free',
      header: 'Available',
      asCurrency: true,
    },
    {
      field: showBotOnly.value && canUseBotBalance.value ? 'est_stake_bot' : 'est_stake',
      header: `in ${botStore.activeBot.balance.stake}`,
      asCurrency: true,
    },
  ];
});

async function refreshBalance() {
  botStore.activeBot.getBalance();
}

onMounted(() => {
  refreshBalance();
});
</script>

<template>
  <div class="ft-balance">
    <div class="ft-balance-bar">
      <SelectButton
        v-if="canUseBotBalance"
        v-model="showBotOnly"
        :options="[
          { value: true, text: 'Bot' },
          { value: false, text: 'Account' },
        ]"
        :allow-empty="false"
        option-label="text"
        option-value="value"
        aria-label="Balance scope"
        size="small"
      />
      <BaseCheckbox v-model="hideSmallBalances">Hide small balances</BaseCheckbox>
      <Button
        severity="secondary"
        size="small"
        class="ms-auto"
        title="Refresh"
        aria-label="Refresh"
        @click="refreshBalance"
      >
        <template #icon><i-mdi-refresh /></template>
      </Button>
    </div>
    <p v-if="botStore.activeBot.balance.note" class="ft-balance-note">
      <i-mdi-information-outline aria-hidden="true" /> {{ botStore.activeBot.balance.note }}
    </p>
    <div class="ft-balance-grid">
      <div class="ft-balance-chart">
        <BalanceChart
          v-if="balanceCurrencies && balanceCurrencies.length"
          :currencies="chartValues"
          :show-title="false"
        />
        <FtEmpty v-else title="No balance to show" />
      </div>
      <DataTable :value="balanceCurrencies" size="small" scrollable>
        <template #empty>No balances.</template>
        <Column
          v-for="(field, idx) in tableFields"
          :key="field.field"
          :field="field.field"
          :header="field.header"
          :class="idx === 0 ? 'ft-mono' : 'ft-num'"
          ><template v-if="field.asCurrency" #body="{ data }">
            {{ formatCurrency(data[field.field]) }}
          </template></Column
        >
        <ColumnGroup type="footer">
          <Row>
            <Column footer="Total" />
            <Column class="ft-num">
              <template #footer>
                <span
                  :class="profitClass(botStore.activeBot.balance.starting_capital_ratio)"
                  :title="`Change against the starting capital of ${formatCurrency(
                    botStore.activeBot.balance.starting_capital,
                  )} ${botStore.activeBot.balance.stake}`"
                >
                  {{ formatSignedPercent(botStore.activeBot.balance.starting_capital_ratio, 2) }}
                </span>
              </template>
            </Column>
            <Column class="ft-num">
              <template #footer>
                {{
                  showBotOnly && canUseBotBalance
                    ? formatCurrency(botStore.activeBot.balance.total_bot)
                    : formatCurrency(botStore.activeBot.balance.total)
                }}
              </template>
            </Column>
          </Row>
        </ColumnGroup>
      </DataTable>
    </div>
  </div>
</template>

<style scoped>
.ft-balance-bar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 14px;
  padding: 8px 12px;
  border-bottom: 1px solid var(--ft-border);
}
.ft-balance-note {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  padding: 8px 18px;
  color: var(--ft-warning);
  font-size: 12px;
  border-bottom: 1px solid var(--ft-border);
}
.ft-balance-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr);
  align-items: start;
}
.ft-balance-chart {
  padding: 8px;
  border-right: 1px solid var(--ft-border);
  min-height: 240px;
  height: 100%;
}
@media (max-width: 1000px) {
  .ft-balance-grid {
    grid-template-columns: minmax(0, 1fr);
  }
  .ft-balance-chart {
    border-right: 0;
    border-bottom: 1px solid var(--ft-border);
  }
}
</style>
