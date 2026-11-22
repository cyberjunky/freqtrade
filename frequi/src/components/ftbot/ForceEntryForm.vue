<script setup lang="ts">
import type { ForceEnterPayload } from '@/types';
import { OrderSides } from '@/types';

const props = withDefaults(
  defineProps<{
    pair?: string;
    positionIncrease?: boolean;
  }>(),
  {
    pair: '',
    positionIncrease: false,
  },
);
const model = defineModel<boolean>();
const botStore = useBotStore();

const form = ref<HTMLFormElement>();
const selectedPair = ref('');
const price = ref<number | undefined>(undefined);
const stakeAmount = ref<number | undefined>(undefined);
const leverage = ref<number | undefined>(undefined);

const ordertype = ref('');
const orderSide = ref<OrderSides>(OrderSides.long);
const enterTag = ref('force_entry');

/** Stake currency the bot can still use: its own share of the wallet where known, else free. */
const availableStake = computed<number | undefined>(() => {
  const stakeBalance = botStore.activeBot.balance.currencies?.find(
    (curr) => curr.currency === botStore.activeBot.stakeCurrency,
  );
  if (!stakeBalance) {
    return undefined;
  }
  return stakeBalance.bot_owned ?? stakeBalance.free;
});

function roundToStakePrecision(value: number): number {
  return Number(value.toFixed(botStore.activeBot.stakeCurrencyDecimals));
}

/** Slider proxy: an empty stake amount (= the bot's configured amount) is 0 on the slider. */
const stakeAmountSlider = computed<number>({
  get: () => stakeAmount.value ?? 0,
  set: (value) => {
    stakeAmount.value = value === 0 ? undefined : value;
  },
});

const stakeStep = computed<number>(() => {
  const precision = 10 ** -botStore.activeBot.stakeCurrencyDecimals;
  return Math.max(roundToStakePrecision((availableStake.value ?? 0) / 100), precision);
});

const stakeRatios = [0.25, 0.5, 0.75, 1];

function applyStakeRatio(ratio: number) {
  if (!availableStake.value) {
    return;
  }
  stakeAmount.value = roundToStakePrecision(availableStake.value * ratio);
}

function onShow() {
  resetForm();
  // Make sure the available balance is current when the dialog opens.
  botStore.activeBot.getBalance();
}

const orderTypeOptions = [
  { value: 'market', text: 'Market' },
  { value: 'limit', text: 'Limit' },
];
const orderSideOptions = [
  { value: 'long', text: 'Long' },
  { value: 'short', text: 'Short' },
];

const checkFormValidity = () => {
  const valid = form.value?.checkValidity();

  return valid;
};

const handleSubmit = async () => {
  // Exit when the form isn't valid
  if (!checkFormValidity()) {
    return;
  }

  // call forceentry
  const payload: ForceEnterPayload = { pair: selectedPair.value };
  if (price.value) {
    payload.price = Number(price.value);
  }
  if (ordertype.value) {
    payload.ordertype = ordertype.value;
  }
  if (stakeAmount.value) {
    payload.stakeamount = stakeAmount.value;
  }
  if (botStore.activeBot.botFeatures.forceEnterShort && botStore.activeBot.shortAllowed) {
    payload.side = orderSide.value;
  }
  if (botStore.activeBot.botFeatures.forceEntryTag && enterTag.value) {
    payload.entry_tag = enterTag.value;
  }

  if (leverage.value) {
    payload.leverage = leverage.value;
  }
  botStore.activeBot.forceentry(payload);
  await nextTick();
  model.value = false;
};
const resetForm = () => {
  console.log('resetForm');
  selectedPair.value = props.pair;
  price.value = undefined;
  stakeAmount.value = undefined;
  ordertype.value =
    botStore.activeBot.botState?.order_types?.forcebuy ||
    botStore.activeBot.botState?.order_types?.force_entry ||
    botStore.activeBot.botState?.order_types?.buy ||
    botStore.activeBot.botState?.order_types?.entry ||
    'limit';
};

const handleEntry = () => {
  // Trigger submit handler
  handleSubmit();
};
</script>

<template>
  <Dialog
    v-model:visible="model"
    :header="positionIncrease ? `Increasing position for ${pair}` : 'Force entering a trade'"
    modal
    @show="onShow"
    @hide="resetForm"
  >
    <form ref="form" class="space-y-4 md:min-w-[32rem]" @submit.prevent="handleSubmit">
      <div v-if="botStore.activeBot.botFeatures.forceEnterShort && botStore.activeBot.shortAllowed">
        <label class="block font-medium mb-1">Order direction (Long or Short)</label>
        <SelectButton
          v-model="orderSide"
          :options="orderSideOptions"
          :allow-empty="false"
          option-label="text"
          option-value="value"
          size="small"
          class="w-full"
        />
      </div>

      <div>
        <label for="pair-input" class="block font-medium mb-1">Pair</label>
        <InputText
          id="pair-input"
          v-model="selectedPair"
          :disabled="positionIncrease"
          required
          class="w-full"
          @keydown.enter="handleEntry"
          @focus="($event.target as HTMLInputElement).select()"
        />
      </div>

      <div>
        <label for="price-input" class="block font-medium mb-1">Price [optional]</label>
        <InputNumber
          id="price-input"
          v-model="price"
          show-buttons
          :min="0"
          :max-fraction-digits="8"
          :step="0.1"
          class="w-full"
          @keydown.enter="handleEntry"
        />
      </div>

      <div>
        <label for="stake-input" class="block font-medium mb-1"
          >* Stake-amount in {{ botStore.activeBot.stakeCurrency }} [optional]</label
        >
        <div class="space-y-2">
          <InputNumber
            id="stake-input"
            v-model="stakeAmount"
            show-buttons
            :min="0"
            :step="['USDC', 'USDT'].includes(botStore.activeBot.stakeCurrency) ? 10 : 1"
            :max-fraction-digits="5"
            fluid
          />
          <template v-if="availableStake">
            <div class="text-sm opacity-75">
              Available:
              {{
                formatPriceCurrency(
                  availableStake,
                  botStore.activeBot.stakeCurrency,
                  botStore.activeBot.stakeCurrencyDecimals,
                )
              }}
            </div>
            <Slider
              v-model="stakeAmountSlider"
              :min="0"
              :max="availableStake"
              :step="stakeStep"
              class="w-full"
            />
            <div class="flex gap-1">
              <Button
                v-for="ratio in stakeRatios"
                :key="ratio"
                size="small"
                severity="secondary"
                class="grow"
                @click="applyStakeRatio(ratio)"
              >
                {{ formatPercent(ratio, 0) }}
              </Button>
              <Button
                size="small"
                severity="secondary"
                title="Use the bot's configured stake amount"
                :disabled="stakeAmount === undefined"
                @click="stakeAmount = undefined"
              >
                Default
              </Button>
            </div>
          </template>
        </div>
      </div>

      <div v-if="botStore.activeBot.botFeatures.forceEnterShort && botStore.activeBot.shortAllowed">
        <label for="leverage-input" class="block font-medium mb-1"
          >Leverage to apply [optional]</label
        >
        <InputNumber
          id="leverage-input"
          v-model="leverage"
          show-buttons
          :min="0"
          :step="1"
          :max-fraction-digits="1"
          class="w-full"
          @keydown.enter="handleEntry"
        />
      </div>

      <div>
        <label class="block text-sm font-medium mb-1">OrderType</label>
        <SelectButton
          v-model="ordertype"
          :options="orderTypeOptions"
          option-label="text"
          option-value="value"
          size="small"
          class="w-full"
        />
      </div>

      <div v-if="botStore.activeBot.botFeatures.forceEntryTag">
        <label for="enterTag-input" class="block text-sm font-medium mb-1"
          >* Custom entry tag [optional]</label
        >
        <InputText id="enterTag-input" v-model="enterTag" class="w-full" />
      </div>
    </form>

    <template #footer>
      <div class="flex justify-end gap-2">
        <Button severity="secondary" size="small" @click="model = false"> Cancel </Button>
        <Button severity="primary" size="small" @click="handleEntry"> Enter Position </Button>
      </div>
    </template>
  </Dialog>
</template>
