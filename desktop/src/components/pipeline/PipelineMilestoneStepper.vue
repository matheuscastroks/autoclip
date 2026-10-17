<script setup lang="ts">
import { computed } from 'vue';
import AppIcon from '../ui/AppIcon.vue';

const props = defineProps<{
  status: string;
  hasTranscript: boolean;
  hasAnalysis: boolean;
  hasCuts: boolean;
  busy?: boolean;
  activeOperation?: string | null;
}>();

interface StepDef {
  id: string;
  title: string;
  subtitle: string;
  state: 'completed' | 'running' | 'current' | 'pending' | 'failed';
}

const steps = computed<StepDef[]>(() => {
  // Step 1: Mídia Importada (sempre concluída no projeto carregado)
  const step1State = 'completed';

  // Step 2: Transcrição
  let step2State: StepDef['state'] = 'pending';
  if (props.hasTranscript) {
    step2State = 'completed';
  } else if (props.status === 'transcribing' || props.activeOperation === 'transcribe') {
    step2State = 'running';
  } else if (props.status === 'failed') {
    step2State = 'failed';
  } else {
    step2State = 'current';
  }

  // Step 3: Análise IA
  let step3State: StepDef['state'] = 'pending';
  if (props.hasAnalysis) {
    step3State = 'completed';
  } else if (props.status === 'analyzing' || props.activeOperation === 'analyze') {
    step3State = 'running';
  } else if (props.status === 'failed' && props.hasTranscript) {
    step3State = 'failed';
  } else if (props.hasTranscript) {
    step3State = 'current';
  } else {
    step3State = 'pending';
  }

  // Step 4: Cortes Prontos
  let step4State: StepDef['state'] = 'pending';
  if (props.hasCuts) {
    step4State = 'completed';
  } else if (props.status === 'rendering' || props.activeOperation === 'render') {
    step4State = 'running';
  } else if (props.status === 'failed' && props.hasAnalysis) {
    step4State = 'failed';
  } else if (props.hasAnalysis) {
    step4State = 'current';
  } else {
    step4State = 'pending';
  }

  return [
    { id: 'media', title: 'Mídia Importada', subtitle: 'Arquivo pronto', state: step1State },
    { id: 'transcribe', title: 'Transcrição', subtitle: 'Áudio em texto', state: step2State },
    { id: 'analyze', title: 'Análise IA', subtitle: 'Ganchos virais', state: step3State },
    { id: 'cuts', title: 'Cortes Prontos', subtitle: 'Clipes 9:16', state: step4State },
  ];
});
</script>

<template>
  <div class="pipeline-milestone-stepper" role="region" aria-label="Progresso do projeto">
    <ol class="stepper-list">
      <li
        v-for="(step, index) in steps"
        :key="step.id"
        class="milestone-step"
        :class="[`is-${step.state}`]"
        :data-step="step.id"
        :data-state="step.state"
      >
        <div class="step-indicator">
          <AppIcon v-if="step.state === 'completed'" name="check" size="sm" class="step-icon" />
          <AppIcon v-else-if="step.state === 'failed'" name="warning" size="sm" class="step-icon" />
          <span v-else-if="step.state === 'running'" class="running-spinner" />
          <span v-else class="step-number">{{ index + 1 }}</span>
        </div>

        <div class="step-info">
          <strong class="step-title">{{ step.title }}</strong>
          <span class="step-subtitle">{{ step.subtitle }}</span>
        </div>

        <div v-if="index < steps.length - 1" class="step-connector" aria-hidden="true" />
      </li>
    </ol>
  </div>
</template>

<style scoped>
.pipeline-milestone-stepper {
  width: 100%;
  padding: 16px 20px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
}

.stepper-list {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  list-style: none;
  margin: 0;
  padding: 0;
  position: relative;
}

.milestone-step {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  position: relative;
  min-width: 0;
}

.step-indicator {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-weight: 700;
  font-size: 13px;
  transition: all 0.2s ease;
  background: var(--color-canvas);
  border: 1.5px solid var(--color-border-subtle);
  color: var(--color-text-muted);
}

.step-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.step-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.step-subtitle {
  font-size: 11px;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.step-connector {
  flex: 1;
  height: 2px;
  background: var(--color-border-subtle);
  margin: 0 8px;
  transition: background 0.2s ease;
}

/* Estados */
.milestone-step.is-completed .step-indicator {
  background: var(--color-success-soft, rgba(52, 211, 153, 0.15));
  border-color: var(--color-success, #34d399);
  color: var(--color-success, #34d399);
}

.milestone-step.is-completed .step-connector {
  background: var(--color-success, #34d399);
}

.milestone-step.is-running .step-indicator {
  background: rgba(175, 198, 213, 0.2);
  border-color: var(--color-action-primary);
  color: var(--color-action-primary);
}

.milestone-step.is-current .step-indicator {
  background: var(--color-surface-raised);
  border-color: var(--color-action-primary);
  color: var(--color-action-primary);
  box-shadow: 0 0 0 3px rgba(175, 198, 213, 0.15);
}

.milestone-step.is-failed .step-indicator {
  background: rgba(248, 113, 113, 0.15);
  border-color: var(--color-danger, #f87171);
  color: var(--color-danger, #f87171);
}

.running-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(175, 198, 213, 0.3);
  border-top-color: var(--color-action-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 900px) {
  .step-subtitle {
    display: none;
  }
  .step-connector {
    margin: 0 4px;
  }
}
</style>
