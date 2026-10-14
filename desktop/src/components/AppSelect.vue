<script setup lang="ts">
import { ElSelect, ElOption } from 'element-plus';

defineOptions({ inheritAttrs: false });
const props = withDefaults(
  defineProps<{
    modelValue: string;
    options: { value: string; label: string; disabled?: boolean }[];
    label: string;
    disabled?: boolean;
    required?: boolean;
  }>(),
  { disabled: false, required: false }
);

const emit = defineEmits<{ 'update:modelValue': [value: string] }>();
</script>

<template>
  <el-select
    v-bind="$attrs"
    role="combobox"
    :model-value="modelValue"
    :disabled="disabled"
    :aria-label="label"
    :placeholder="label"
    class="app-select ui-control"
    @update:model-value="(val: string) => emit('update:modelValue', val)"
  >
    <el-option
      v-for="option in options"
      :key="option.value"
      :value="option.value"
      :label="option.label"
      :disabled="option.disabled"
    />
  </el-select>
</template>
