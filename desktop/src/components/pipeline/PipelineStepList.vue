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
    :aria-label="technical ? 'Etapas técnicas' : 'Etapas de preparação'"
  >
    <li
      v-for="step in steps"
      :key="step.id"
      :data-stage="technical ? step.id : undefined"
      :data-milestone="!technical ? step.id : undefined"
      :data-state="step.state"
    >
      <AppIcon
        :name="
          step.state === 'completed'
            ? 'check'
            : ['failed', 'interrupted', 'cancelled'].includes(step.state)
              ? 'warning'
              : 'clock'
        "
        size="sm"
      />
      <div class="pipeline-step-body">
        <div class="pipeline-step-heading">
          <strong>{{ step.title }}</strong
          ><span>{{
            step.state === 'waiting' ? 'Aguardando seleção' : labels[step.state] || step.state
          }}</span>
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
  gap: 16px;
}
li {
  display: flex;
  align-items: start;
  gap: 12px;
  min-width: 0;
  color: var(--color-text-secondary);
}
li > svg {
  margin-top: 3px;
}
.pipeline-step-body {
  min-width: 0;
  width: 100%;
}
.pipeline-step-heading {
  display: flex;
  align-items: baseline;
  gap: 16px;
  justify-content: space-between;
  flex-wrap: wrap;
}
strong {
  font-size: var(--font-size-body);
  font-weight: 500;
  color: var(--color-text-primary);
}
.pipeline-step-heading span {
  font-size: var(--font-size-meta);
}
.pipeline-step-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}
.stage-progress {
  height: 3px;
  margin-top: 8px;
  max-width: 560px;
}
</style>
