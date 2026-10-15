<script setup lang="ts">
import { computed } from 'vue';
import { getIcon, type IconName } from './icons';

const props = withDefaults(
  defineProps<{
    name: IconName;
    size?: 'sm' | 'md' | 'lg';
    variant?: 'regular' | 'filled';
    decorative?: boolean;
    label?: string;
  }>(),
  { size: 'md', variant: 'regular', decorative: true }
);

const icon = computed(() => getIcon(props.name));
const component = computed(() =>
  props.variant === 'filled' ? icon.value?.filled || icon.value?.regular : icon.value?.regular
);
</script>

<template>
  <component
    :is="component"
    v-if="icon"
    class="app-icon"
    :class="'app-icon--' + size"
    :aria-hidden="decorative ? 'true' : undefined"
    :role="decorative ? undefined : 'img'"
    :aria-label="decorative ? undefined : label || icon.label"
    focusable="false"
  />
</template>

<style scoped>
.app-icon {
  display: inline-block;
  flex: none;
  width: var(--app-icon-size);
  height: var(--app-icon-size);
  color: inherit;
  vertical-align: middle;
}
.app-icon--sm {
  --app-icon-size: 16px;
}
.app-icon--md {
  --app-icon-size: 20px;
}
.app-icon--lg {
  --app-icon-size: 24px;
}
</style>
