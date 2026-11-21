<script setup lang="ts">
import type { BotUiMode } from '@/composables/botInfo';

/** Mode badge. DRY-RUN = neutral grey bordered, LIVE = amber tint (signals real money). */
defineProps<{ mode: BotUiMode }>();
</script>

<template>
  <FtBadge v-if="mode === 'live'" kind="warn" title="Live trading - real money">LIVE</FtBadge>
  <FtBadge v-else-if="mode === 'dry'" kind="neutral" title="Dry-run - simulated trades">
    DRY-RUN
  </FtBadge>
  <FtBadge v-else-if="mode === 'webserver'" kind="default" title="Webserver mode - no trading">
    WEBSERVER
  </FtBadge>
  <FtBadge v-else kind="neutral" title="Mode unknown - bot not reachable">UNKNOWN</FtBadge>
</template>
