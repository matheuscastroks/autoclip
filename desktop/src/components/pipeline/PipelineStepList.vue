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
      <!-- Overview / Milestone Item -->
      <template v-if="!technical">
        <div class="milestone-left">
          <div class="milestone-marker">
            <AppIcon v-if="step.state === 'completed'" name="check" size="sm" class="step-icon" />
            <span v-else class="milestone-number">{{ index + 1 }}</span>
          </div>
          <strong class="step-title">{{ step.title }}</strong>
        </div>
        <span
          class="step-state-badge"
          :data-state="step.state"
        >
          {{ step.state === 'waiting' ? 'Aguardando seleção' : labels[step.state] || step.state }}
        </span>
      </template>

      <!-- Technical Stage Item -->
      <template v-else>
        <div class="technical-index" :data-state="step.state">
          <AppIcon
            v-if="step.state === 'completed'"
            name="check"
            size="sm"
            class="step-icon"
          />
          <AppIcon
            v-else-if="['failed', 'interrupted', 'cancelled'].includes(step.state)"
            name="warning"
            size="sm"
            class="step-icon"
          />
          <span v-else class="index-num">{{ String(index + 1).padStart(2, '0') }}</span>
        </div>

        <div class="pipeline-step-body">
          <div class="pipeline-step-heading">
            <strong class="step-title" :title="step.title">{{ step.title }}</strong>
            <span class="step-state-pill" :data-state="step.state">
              <span v-if="step.state === 'running'" class="pill-dot" />
              {{ step.state === 'waiting' ? 'Aguardando' : labels[step.state] || step.state }}
            </span>
          </div>

          <div
            v-if="!['pending', 'waiting'].includes(step.state)"
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
      </template>
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

/* Overview Milestones List (Vertical inside subgrid card) */
.pipeline-step-list--overview {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.milestone-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  border-radius: var(--radius-control);
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
  transition: border-color 0.15s ease, background-color 0.15s ease;
  min-width: 0;
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

.milestone-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.milestone-marker {
  width: 24px;
  height: 24px;
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
  white-space: nowrap;
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

.milestone-item .step-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Technical Engine Stages - Full Column Vertical List */
.pipeline-step-list--technical {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.technical-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  border-radius: var(--radius-control);
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
  transition: border-color 0.15s ease, background-color 0.15s ease;
  min-width: 0;
  color: var(--color-text-secondary);
}

.technical-item:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-border-strong);
}

.technical-item[data-state='completed'] {
  border-color: rgba(52, 211, 153, 0.2);
  background: rgba(52, 211, 153, 0.03);
}

.technical-item[data-state='running'] {
  border-color: rgba(175, 198, 213, 0.45);
  background: rgba(175, 198, 213, 0.08);
}

.technical-item[data-state='failed'],
.technical-item[data-state='interrupted'],
.technical-item[data-state='cancelled'] {
  border-color: rgba(248, 113, 113, 0.35);
  background: rgba(248, 113, 113, 0.05);
}

.technical-index {
  width: 22px;
  height: 22px;
  border-radius: var(--radius-subtle, 4px);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: var(--color-canvas);
  border: 1px solid var(--color-border-subtle);
  font-family: var(--font-mono, monospace);
  font-size: 10px;
  font-weight: 600;
  color: var(--color-text-muted);
  line-height: 1;
}

.technical-index .step-icon {
  width: 12px;
  height: 12px;
}

.technical-index[data-state='completed'] {
  background: var(--color-success-soft);
  border-color: var(--color-success-border);
  color: var(--color-success);
}

.technical-index[data-state='running'] {
  background: rgba(175, 198, 213, 0.18);
  border-color: var(--color-action-primary);
  color: var(--color-action-primary);
}

.technical-index[data-state='failed'],
.technical-index[data-state='interrupted'],
.technical-index[data-state='cancelled'] {
  background: rgba(248, 113, 113, 0.15);
  border-color: var(--color-danger);
  color: var(--color-danger);
}

.pipeline-step-body {
  min-width: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.pipeline-step-heading {
  display: flex;
  align-items: center;
  gap: 6px;
  justify-content: space-between;
}

.step-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.technical-item .step-title {
  font-size: 11px;
  font-weight: 500;
  letter-spacing: -0.01em;
}

.step-state-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 500;
  color: var(--color-text-muted);
  flex-shrink: 0;
  line-height: 1;
}

.step-state-pill .pill-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--color-action-primary);
}

.step-state-pill[data-state='completed'] {
  color: var(--color-success);
}

.step-state-pill[data-state='running'] {
  color: var(--color-action-primary);
}

.step-state-pill[data-state='failed'],
.step-state-pill[data-state='interrupted'],
.step-state-pill[data-state='cancelled'] {
  color: var(--color-danger);
}

.pipeline-step-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.pipeline-step-actions :deep(.button),
.pipeline-step-actions button {
  padding: 2px 8px;
  font-size: 11px;
  height: auto;
}

.stage-progress {
  height: 2px;
  margin-top: 4px;
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

@media (max-width: 900px) {
  .pipeline-step-list--technical {
    grid-template-columns: 1fr;
  }
}
</style>
