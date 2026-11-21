<script setup lang="ts" generic="T extends string | number">
import type { RouteLocationRaw } from 'vue-router';

/**
 * Segmented tabs: track (page bg, border) with 28px tabs, active = primary.
 * Either `v-model` driven (buttons, role=tab) or router driven (items with `to`).
 */
export interface SegmentedItem<V> {
  value: V;
  label: string;
  to?: RouteLocationRaw;
  title?: string;
  disabled?: boolean;
}

const props = withDefaults(
  defineProps<{
    items: SegmentedItem<T>[];
    label?: string;
    small?: boolean;
  }>(),
  { label: undefined, small: false },
);

const model = defineModel<T>();

function onKey(ev: KeyboardEvent, idx: number) {
  if (ev.key !== 'ArrowRight' && ev.key !== 'ArrowLeft') return;
  const list = (ev.currentTarget as HTMLElement).parentElement;
  if (!list) return;
  const els = Array.from(list.querySelectorAll<HTMLElement>('.ft-seg-tab:not([disabled])'));
  const cur = els.indexOf(ev.currentTarget as HTMLElement);
  const next = els[(cur + (ev.key === 'ArrowRight' ? 1 : -1) + els.length) % els.length];
  next?.focus();
  const item = props.items[idx];
  if (item && !item.to) next?.click();
  ev.preventDefault();
}
</script>

<template>
  <div class="ft-seg" :class="{ 'is-small': small }" role="tablist" :aria-label="label">
    <template v-for="(item, idx) in items" :key="item.value">
      <RouterLink
        v-if="item.to"
        :to="item.to"
        class="ft-seg-tab"
        :class="{ 'is-active': model === item.value }"
        role="tab"
        :aria-selected="model === item.value"
        :title="item.title"
        @keydown="onKey($event, idx)"
      >
        <slot name="item" :item="item">{{ item.label }}</slot>
      </RouterLink>
      <button
        v-else
        type="button"
        class="ft-seg-tab"
        :class="{ 'is-active': model === item.value }"
        role="tab"
        :aria-selected="model === item.value"
        :tabindex="model === item.value || model === undefined ? 0 : -1"
        :disabled="item.disabled"
        :title="item.title"
        @click="model = item.value"
        @keydown="onKey($event, idx)"
      >
        <slot name="item" :item="item">{{ item.label }}</slot>
      </button>
    </template>
  </div>
</template>
