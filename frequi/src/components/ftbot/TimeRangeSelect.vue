<script setup lang="ts">
import { VueDatePicker } from '@vuepic/vue-datepicker';
import '@vuepic/vue-datepicker/dist/main.css';

const settingsStore = useSettingsStore();

const now = new Date();
const tomorrow = new Date();
tomorrow.setDate(tomorrow.getDate() + 1);
const dateFrom = ref<string>('');
const dateTo = ref<string>('');

const props = withDefaults(
  defineProps<{
    modelValue: string;
  }>(),
  {},
);
const emit = defineEmits<{ 'update:modelValue': [value: string] }>();

const timeRange = computed(() => {
  if (dateFrom.value !== '' || dateTo.value !== '') {
    return `${dateStringToTimeRange(dateFrom.value)}-${dateStringToTimeRange(dateTo.value)}`;
  }
  return '';
});

function updateInput() {
  const tr = props.modelValue.split('-');
  if (tr[0]) {
    dateFrom.value = timestampToDateString(
      tr[0].length === 8 ? dateFromString(tr[0], 'yyyyMMdd') : parseInt(tr[0]) * 1000,
    );
  } else {
    dateFrom.value = '';
  }
  if (tr.length > 1 && tr[1]) {
    dateTo.value = timestampToDateString(
      tr[1].length === 8 ? dateFromString(tr[1], 'yyyyMMdd') : parseInt(tr[1]) * 1000,
    );
  } else {
    dateTo.value = '';
  }
  emit('update:modelValue', timeRange.value);
}

watch(
  () => timeRange.value,
  () => emit('update:modelValue', timeRange.value),
);
watch(
  () => props.modelValue,
  () => {
    updateInput();
  },
);

onMounted(() => {
  if (!props.modelValue) {
    dateFrom.value = timestampToDateString(new Date(now.getFullYear(), now.getMonth() - 1, 1));
  } else {
    updateInput();
  }
  emit('update:modelValue', timeRange.value);
});
</script>

<template>
  <div>
    <div class="flex flex-wrap gap-3">
      <div>
        <label for="dateFrom" class="ft-label">Start date</label>
        <VueDatePicker
          id="dateFrom"
          v-model="dateFrom"
          :dark="settingsStore.isDarkTheme"
          :max-date="now"
          model-type="yyyy-MM-dd"
          :formats="{ input: 'yyyy-MM-dd', preview: 'yyyy-MM-dd' }"
          text-input
          auto-apply
          :time-config="{ enableTimePicker: false }"
        ></VueDatePicker>
      </div>
      <div>
        <label for="dateTo" class="ft-label">End date</label>
        <VueDatePicker
          id="dateTo"
          v-model="dateTo"
          :dark="settingsStore.isDarkTheme"
          :max-date="tomorrow"
          model-type="yyyy-MM-dd"
          :formats="{ input: 'yyyy-MM-dd', preview: 'yyyy-MM-dd' }"
          text-input
          auto-apply
          :time-config="{ enableTimePicker: false }"
        ></VueDatePicker>
      </div>
    </div>

    <label class="ft-hint block mt-1">
      Timerange: <b class="ft-mono">{{ timeRange || 'not set' }}</b>
    </label>
  </div>
</template>
