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
  border-top: 1px solid var(--color-border-subtle);
  min-width: 0;
}
summary {
  padding: 16px 0;
  cursor: pointer;
  color: var(--color-text-secondary);
  font-weight: 500;
  font-size: var(--font-size-control);
}
.technical-details-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 0 0 16px;
  min-width: 0;
}
</style>
