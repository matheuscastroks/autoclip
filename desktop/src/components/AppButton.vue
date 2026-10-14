<script setup lang="ts">
import { computed, useAttrs } from 'vue';
import { ElButton } from 'element-plus';

defineOptions({ inheritAttrs: false });
const attrs = useAttrs();

const nativeType = computed<'button' | 'submit' | 'reset'>(() => {
  const t = attrs.type as string | undefined;
  if (t === 'submit' || t === 'reset' || t === 'button') return t;
  return 'button';
});

const elType = computed<
  'default' | 'primary' | 'success' | 'warning' | 'info' | 'danger' | 'text' | undefined
>(() => {
  const t = attrs.type as string | undefined;
  if (['primary', 'success', 'warning', 'danger', 'info', 'text', 'default'].includes(t || '')) {
    return t as any;
  }
  return undefined;
});

const filteredAttrs = computed(() => {
  const { type, ...rest } = attrs;
  return rest;
});
</script>

<template>
  <el-button v-bind="filteredAttrs" :type="elType" :native-type="nativeType" class="ui-control">
    <slot />
  </el-button>
</template>
