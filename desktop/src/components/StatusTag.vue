<script setup lang="ts">
import { computed } from 'vue';
import { statusTagType, type StatusTagType } from '../domain/jobStatus';
import { labels } from '../format';

const props = withDefaults(
  defineProps<{
    status: string;
    label?: string;
    size?: 'small' | 'default' | 'large';
    effect?: 'dark' | 'light' | 'plain';
    round?: boolean;
  }>(),
  {
    size: 'small',
    effect: 'light',
    round: false,
  }
);

const tagType = computed<StatusTagType>(() => statusTagType(props.status));
const displayLabel = computed(() => props.label || labels[props.status] || props.status);
</script>

<template>
  <el-tag
    :type="tagType"
    :size="size"
    :effect="effect"
    :round="round"
    class="status-tag"
    :data-status="status"
  >
    <slot>{{ displayLabel }}</slot>
  </el-tag>
</template>

<style scoped>
.status-tag {
  font-weight: 500;
  letter-spacing: 0.01em;
}
</style>
