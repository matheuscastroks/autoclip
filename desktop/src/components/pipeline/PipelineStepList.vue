<script setup lang="ts">
import AppButton from '../AppButton.vue';
import AppIcon from '../ui/AppIcon.vue';
import type { StepId, StepState } from '../../composables/usePipelineSteps';
import type { PipelineAction } from '../../composables/usePipelinePresentation';
import { labels } from '../../format';
defineProps<{
  steps: { id: StepId; title: string; state: StepState; actions: PipelineAction[] }[];
  technical?: boolean;
}>();
defineEmits<{ action: [value: PipelineAction] }>();
</script>

<template>
  <ol
    class="pipeline-step-list"
    :class="{
      'pipeline-step-list--technical': technical,
      'pipeline-step-list--overview': !technical,
    }"
    :aria-label="technical ? 'Etapas técnicas' : 'Etapas de preparação'"
  >
    <li
      v-for="(step, index) in steps"
      :key="step.id"
      :data-stage="technical ? step.id : undefined"
      :data-milestone="!technical ? step.id : undefined"
      :data-state="step.state"
      :class="technical ? 'technical-item' : 'milestone-item'"
    >
      <div v-if="!technical" class="milestone-marker">
        <AppIcon v-if="step.state === 'completed'" name="check" size="sm" class="step-icon" />
        <span v-else class="milestone-number">{{ index + 1 }}</span>
      </div>
      <AppIcon
        v-else
        :name="
          step.state === 'completed'
            ? 'check'
            : ['failed', 'interrupted', 'cancelled'].includes(step.state)
              ? 'warning'
              : 'clock'
        "
        size="sm"
        class="step-icon"
      />

      <div class="pipeline-step-body">
        <div class="pipeline-step-heading">
          <strong class="step-title">{{ step.title }}</strong>
          <span
            :class="!technical ? 'step-state-badge' : 'step-state-text'"
            :data-state="step.state"
          >
            {{ step.state === 'waiting' ? 'Aguardando seleção' : labels[step.state] || step.state }}
          </span>
        </div>

        <div
          v-if="technical && !['pending', 'waiting'].includes(step.state)"
          role="progressbar"
          :aria-label="step.title"
          :aria-valuenow="step.state === 'completed' ? 100 : undefined"
          class="stage-progress"
          :class="{
            indeterminate: ['running', 'cancelling'].includes(step.state),
            complete: step.state === 'completed',
          }"
        >
          <span />
        </div>

        <div v-if="step.actions.length" class="pipeline-step-actions">
          <AppButton
            v-for="action in step.actions"
            :key="action.id"
            class="button secondary small"
            :disabled="action.disabled"
            @click="$emit('action', action)"
            >{{ action.label }}</AppButton
          >
        </div>
      </div>
    </li>
  </ol>
</template>

<style scoped>
.pipeline-step-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
}

/* Overview Milestones List */
.pipeline-step-list--overview {
  gap: 10px;
}

.milestone-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 14px;
  border-radius: var(--radius-control);
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
  transition: border-color 0.15s ease, background-color 0.15s ease;
}

.milestone-item:hover {
  border-color: var(--color-border-strong);
}

.milestone-item[data-state='running'] {
  border-color: rgba(175, 198, 213, 0.4);
  background: rgba(175, 198, 213, 0.05);
}

.milestone-item[data-state='completed'] {
  border-color: rgba(52, 211, 153, 0.25);
  background: rgba(52, 211, 153, 0.03);
}

.milestone-marker {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: var(--color-canvas);
  border: 1px solid var(--color-border-subtle);
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.milestone-item[data-state='completed'] .milestone-marker {
  background: var(--color-success-soft);
  border-color: var(--color-success-border);
  color: var(--color-success);
}

.milestone-item[data-state='running'] .milestone-marker {
  background: rgba(175, 198, 213, 0.15);
  border-color: var(--color-action-primary);
  color: var(--color-action-primary);
}

.milestone-number {
  line-height: 1;
}

.step-state-badge {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--color-canvas);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-subtle);
}

.milestone-item[data-state='completed'] .step-state-badge {
  color: var(--color-success);
  border-color: var(--color-success-border);
  background: var(--color-success-soft);
}

.milestone-item[data-state='running'] .step-state-badge {
  color: var(--color-action-primary);
  border-color: rgba(175, 198, 213, 0.4);
  background: rgba(175, 198, 213, 0.12);
}

/* Technical Items Styling */
.pipeline-step-list--technical {
  gap: 4px;
}

.technical-item {
  display: flex;
  align-items: start;
  gap: 10px;
  padding: 6px 8px;
  border-radius: var(--radius-control);
  background: transparent;
  transition: background-color 0.15s ease;
  min-width: 0;
  color: var(--color-text-secondary);
}

.technical-item:hover {
  background: var(--color-surface-hover);
}

.technical-item > svg,
.technical-item > .step-icon {
  margin-top: 3px;
  flex-shrink: 0;
}

.technical-item[data-state='completed'] > svg,
.technical-item[data-state='completed'] > .step-icon {
  color: var(--color-success);
}

.technical-item[data-state='running'] > svg,
.technical-item[data-state='running'] > .step-icon {
  color: var(--color-action-primary);
}

.technical-item[data-state='failed'] > svg,
.technical-item[data-state='interrupted'] > svg,
.technical-item[data-state='cancelled'] > svg,
.technical-item[data-state='failed'] > .step-icon,
.technical-item[data-state='interrupted'] > .step-icon,
.technical-item[data-state='cancelled'] > .step-icon {
  color: var(--color-danger);
}

.technical-item[data-state='pending'] > svg,
.technical-item[data-state='waiting'] > svg,
.technical-item[data-state='pending'] > .step-icon,
.technical-item[data-state='waiting'] > .step-icon {
  color: var(--color-text-muted);
  opacity: 0.6;
}

.pipeline-step-body {
  min-width: 0;
  width: 100%;
}

.pipeline-step-heading {
  display: flex;
  align-items: baseline;
  gap: 12px;
  justify-content: space-between;
  flex-wrap: wrap;
}

strong {
  font-size: var(--font-size-body);
  font-weight: 500;
  color: var(--color-text-primary);
}

.technical-item strong {
  font-size: 13px;
}

.step-state-text {
  font-size: 11px;
  color: var(--color-text-secondary);
}

.pipeline-step-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.stage-progress {
  height: 3px;
  margin-top: 6px;
  max-width: 100%;
  background: var(--color-canvas);
  border-radius: 999px;
  overflow: hidden;
}

.stage-progress > span {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: var(--color-action-primary);
  transition: width 0.3s ease;
}

.stage-progress.complete > span {
  background: var(--color-success);
  width: 100% !important;
}

.stage-progress.indeterminate > span {
  width: 40%;
  animation: indeterminate-shimmer 1.5s infinite ease-in-out alternate;
}

@keyframes indeterminate-shimmer {
  0% { transform: translateX(0%); }
  100% { transform: translateX(150%); }
}
</style>
