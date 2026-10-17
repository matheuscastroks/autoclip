<script setup lang="ts">
import AppIcon from './AppIcon.vue';

const open = defineModel<boolean>({ default: false });
defineProps<{
  title?: string;
  badge?: string;
  badgeType?: 'default' | 'active' | 'success' | 'warning' | 'error';
}>();
</script>

<template>
  <details
    class="technical-details"
    :open="open"
    @toggle="open = ($event.target as HTMLDetailsElement).open"
  >
    <summary class="technical-details-summary">
      <div class="summary-main">
        <span class="summary-icon">
          <AppIcon name="cpu" size="sm" />
        </span>
        <span class="summary-title">{{ title || 'Detalhes técnicos' }}</span>
        <span v-if="badge" class="summary-badge" :class="badgeType || 'default'">
          <span v-if="badgeType === 'active'" class="status-indicator-dot" />
          {{ badge }}
        </span>
      </div>
      <div class="summary-actions">
        <svg class="summary-chevron" viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
          <path
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M4 6l4 4 4-4"
          />
        </svg>
      </div>
    </summary>
    <div class="technical-details-content">
      <slot />
    </div>
  </details>
</template>

<style scoped>
.technical-details {
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
  background: var(--color-surface);
  min-width: 0;
  overflow: hidden;
  transition: border-color 0.2s ease, background-color 0.2s ease;
}

.technical-details:hover {
  border-color: var(--color-border-strong);
}

.technical-details[open] {
  background: var(--color-surface);
  border-color: var(--color-border-subtle);
}

.technical-details-summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  user-select: none;
  list-style: none;
  background: var(--color-surface);
  transition: background-color 0.15s ease;
}

.technical-details-summary::-webkit-details-marker {
  display: none;
}

.technical-details-summary:hover {
  background: var(--color-surface-hover);
}

.technical-details-summary:focus-visible {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: -2px;
}

.summary-main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.summary-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-action-primary);
  opacity: 0.85;
}

.summary-title {
  font-size: var(--font-size-control);
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

.summary-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 500;
  border-radius: 999px;
  line-height: 1.3;
}

.summary-badge.default {
  background: var(--color-surface-raised);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-subtle);
}

.summary-badge.active {
  background: rgba(175, 198, 213, 0.12);
  color: var(--color-action-primary);
  border: 1px solid rgba(175, 198, 213, 0.3);
}

.summary-badge.success {
  background: var(--color-success-soft);
  color: var(--color-success);
  border: 1px solid var(--color-success-border);
}

.summary-badge.warning {
  background: var(--color-warning-surface);
  color: var(--color-warning-text);
  border: 1px solid var(--color-warning-border);
}

.summary-badge.error {
  background: var(--color-danger-soft);
  color: var(--color-danger);
  border: 1px solid var(--color-danger-border);
}

.status-indicator-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--color-action-primary);
}

.summary-actions {
  display: flex;
  align-items: center;
  color: var(--color-text-secondary);
}

.summary-chevron {
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), color 0.15s ease;
}

.technical-details[open] .summary-chevron {
  transform: rotate(180deg);
  color: var(--color-text-primary);
}

.technical-details-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 14px 16px 18px;
  min-width: 0;
  border-top: 1px solid var(--color-border-subtle);
}
</style>
