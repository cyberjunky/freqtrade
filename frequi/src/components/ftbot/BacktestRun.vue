<script setup lang="ts">
import type { BacktestPayload } from '@/types';

const botStore = useBotStore();
const btStore = useBtStore();

function clickBacktest() {
  const btPayload: BacktestPayload = {
    strategy: btStore.strategy,
    timerange: btStore.timerange,
    enable_protections: btStore.enableProtections,
  };
  if (btStore.maxOpenTrades) {
    btPayload.max_open_trades = btStore.maxOpenTrades;
  }
  if (btStore.stakeAmountUnlimited) {
    btPayload.stake_amount = 'unlimited';
  } else {
    const stakeAmountLoc = Number(btStore.stakeAmount);
    if (stakeAmountLoc) {
      btPayload.stake_amount = stakeAmountLoc.toString();
    }
  }

  const startingCapitalLoc = Number(btStore.startingCapital);
  if (startingCapitalLoc) {
    btPayload.dry_run_wallet = startingCapitalLoc;
  }

  if (btStore.selectedTimeframe) {
    btPayload.timeframe = btStore.selectedTimeframe;
  }
  if (btStore.selectedDetailTimeframe) {
    btPayload.timeframe_detail = btStore.selectedDetailTimeframe;
  }
  if (!btStore.allowCache) {
    btPayload.backtest_cache = 'none';
  }
  botStore.activeBot.startBacktest(btPayload);
}
</script>

<template>
  <div class="ft-stack ft-btrun">
    <FtPanel title="Backtesting parameters">
      <div class="ft-btrun-grid">
        <div class="ft-btrun-wide">
          <span class="ft-label">Strategy</span>
          <StrategySelect v-model="btStore.strategy"></StrategySelect>
        </div>

        <div>
          <label for="timeframe-select" class="ft-label">Timeframe</label>
          <TimeframeSelect id="timeframe-select" v-model="btStore.selectedTimeframe" />
        </div>
        <div>
          <label for="timeframe-detail-select" class="ft-label ft-label-info"
            >Detail timeframe
            <InfoBox
              hint="Detail timeframe, to simulate intra-candle results. Not setting this will not use this functionality."
            />
          </label>
          <TimeframeSelect
            id="timeframe-detail-select"
            v-model="btStore.selectedDetailTimeframe"
            :below-timeframe="btStore.selectedTimeframe"
          />
        </div>

        <div>
          <label for="max-open-trades" class="ft-label">Max open trades</label>
          <InputNumber
            v-model="btStore.maxOpenTrades"
            input-id="max-open-trades"
            placeholder="Use strategy default"
            class="w-full"
          ></InputNumber>
        </div>
        <div>
          <label for="starting-capital" class="ft-label">Starting capital</label>
          <InputNumber
            v-model="btStore.startingCapital"
            input-id="starting-capital"
            placeholder="Use config default"
            :step="0.001"
            :max-fraction-digits="8"
            class="w-full"
          ></InputNumber>
        </div>
        <div>
          <label for="stake-amount" class="ft-label">Stake amount</label>
          <InputNumber
            v-model="btStore.stakeAmount"
            input-id="stake-amount"
            placeholder="Use strategy default"
            :step="0.01"
            :max-fraction-digits="8"
            :disabled="btStore.stakeAmountUnlimited"
            class="w-full"
          ></InputNumber>
          <BaseCheckbox v-model="btStore.stakeAmountUnlimited" class="mt-2"
            >Unlimited stake</BaseCheckbox
          >
        </div>
        <div class="ft-btrun-checks">
          <BaseCheckbox v-model="btStore.enableProtections">Enable protections</BaseCheckbox>
          <BaseCheckbox
            v-if="botStore.activeBot.botFeatures.backtestCache"
            v-model="btStore.allowCache"
            >Cache backtest results</BaseCheckbox
          >
        </div>

        <div class="ft-btrun-wide">
          <TimeRangeSelect v-model="btStore.timerange"></TimeRangeSelect>
        </div>
      </div>
    </FtPanel>

    <div class="ft-btrun-actions">
      <Button
        id="start-backtest"
        severity="primary"
        :disabled="
          !btStore.canRunBacktest ||
          botStore.activeBot.backtestRunning ||
          !botStore.activeBot.canRunBacktest
        "
        @click="clickBacktest"
      >
        Start backtest
      </Button>
      <Button
        severity="secondary"
        :disabled="botStore.activeBot.backtestRunning || !botStore.activeBot.canRunBacktest"
        @click="botStore.activeBot.pollBacktest"
      >
        Load backtest result
      </Button>
      <Button
        severity="secondary"
        :disabled="!botStore.activeBot.backtestRunning"
        @click="botStore.activeBot.stopBacktest"
      >
        Stop backtest
      </Button>
      <Button
        severity="secondary"
        :disabled="botStore.activeBot.backtestRunning || !botStore.activeBot.canRunBacktest"
        @click="botStore.activeBot.removeBacktest"
      >
        Reset backtest
      </Button>
    </div>
  </div>
</template>

<style lang="css" scoped>
.ft-btrun {
  max-width: 860px;
}
.ft-btrun-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px 18px;
  align-items: start;
}
.ft-btrun-wide {
  grid-column: 1 / -1;
}
.ft-btrun-checks {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 18px;
}
.ft-label-info {
  display: flex;
  align-items: center;
  gap: 6px;
}
.ft-btrun-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
@media (max-width: 700px) {
  .ft-btrun-grid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
