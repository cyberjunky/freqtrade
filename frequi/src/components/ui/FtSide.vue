<script setup lang="ts">
/** Side tag: LONG (green tint) / SHORT (red tint). */
defineProps<{ short?: boolean }>();
</script>

<template>
  <FtBadge :kind="short ? 'bad' : 'ok'">{{ short ? 'SHORT' : 'LONG' }}</FtBadge>
</template>
