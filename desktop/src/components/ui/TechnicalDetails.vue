<script setup lang="ts">
const open = defineModel<boolean>({ default: false });
defineProps<{ title?: string }>();
</script>

<template>
  <details
    class="technical-details"
    :open="open"
    @toggle="open = ($event.target as HTMLDetailsElement).open"
  >
    <summary>{{ title || 'Detalhes técnicos' }}</summary>
    <div class="technical-details-content"><slot /></div>
  </details>
</template>

<style scoped>
.technical-details {
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
  background: var(--color-surface);
  min-width: 0;
  overflow: hidden;
}
summary {
  padding: 14px 16px;
  cursor: pointer;
  color: var(--color-text-secondary);
  font-weight: 500;
  font-size: var(--font-size-control);
}
.technical-details-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 0 16px 16px;
  min-width: 0;
}
</style>
