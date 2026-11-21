<script setup lang="ts">
const botStore = useBotStore();
</script>

<template>
  <div class="ft-login">
    <div class="ft-login-card">
      <div class="ft-login-brand">
        <i-mdi-chart-line class="ft-login-icon" aria-hidden="true" />
        <span>FREQTRADE</span>
      </div>
      <h1 class="ft-page-title card-header">Freqtrade bot Login</h1>
      <p class="ft-hint ft-login-sub">
        Connect this browser to the REST API of a Freqtrade bot.
        <span v-if="botStore.hasBots">The bot is added next to the ones already connected.</span>
      </p>
      <BotLogin ref="loginForm" />
    </div>
    <p class="ft-hint ft-login-foot">
      Need help? See the
      <a href="https://www.freqtrade.io/en/latest/rest-api/" target="_blank" rel="noopener"
        >REST API documentation</a
      >.
    </p>
  </div>
</template>

<style scoped>
.ft-login {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 16px 32px;
  gap: 14px;
}
.ft-login-card {
  width: 100%;
  max-width: 420px;
  background: var(--ft-panel);
  border: 1px solid var(--ft-border);
  border-radius: var(--ft-radius-panel);
  padding: 22px 24px 20px;
}
.ft-login-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  letter-spacing: 0.12em;
  font-size: 12px;
  color: var(--ft-text-2);
  margin-bottom: 14px;
}
.ft-login-icon {
  color: var(--ft-primary);
  font-size: 18px;
}
.ft-login-sub {
  margin: 4px 0 16px;
}
.ft-login-foot {
  margin: 0;
}
@media (max-width: 700px) {
  .ft-login {
    padding-top: 20px;
  }
  .ft-login-card {
    padding: 18px 16px;
  }
}
</style>
