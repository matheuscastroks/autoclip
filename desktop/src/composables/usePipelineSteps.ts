import { computed, type Ref } from 'vue';
import type { Job, Project, Revision } from '../types';

export type StepId =
  | 'import'
  | 'audio'
  | 'transcribe'
  | 'analyze'
  | 'choose'
  | 'edit_plan'
  | 'reframe'
  | 'captions'
  | 'render'
  | 'verify'
  | 'export';

export type StepState =
  | 'completed'
  | 'waiting'
  | 'pending'
  | 'running'
  | 'cancelling'
  | 'failed'
  | 'cancelled'
  | 'interrupted';

export const PIPELINE_STEPS: readonly [StepId, string][] = [
  ['import', 'Importar'],
  ['audio', 'Áudio'],
  ['transcribe', 'Transcrever'],
  ['analyze', 'Análise'],
  ['choose', 'Escolher cortes'],
  ['edit_plan', 'Plano'],
  ['reframe', 'Enquadrar'],
  ['captions', 'Legendas'],
  ['render', 'Renderizar'],
  ['verify', 'Verificar'],
  ['export', 'Exportar'],
] as const;

export interface UsePipelineStepsOptions {
  project: Ref<Project>;
  job: Ref<Job | undefined>;
  revisions: Ref<Revision[] | undefined>;
  selectedCount: Ref<number>;
  importRecovery: Ref<boolean>;
  hasCuts: Ref<boolean>;
}

export function usePipelineSteps(options: UsePipelineStepsOptions) {
  const { project, job, revisions, selectedCount, importRecovery, hasCuts } = options;

  function calculateState(step: string): StepState {
    if (step === 'choose') {
      return selectedCount.value
        ? 'completed'
        : project.value.has_analysis
          ? 'waiting'
          : 'pending';
    }
    if (step === 'export' && revisions.value?.some(r => r.exported)) {
      return 'completed';
    }
    if (step === 'import' && importRecovery.value && job.value) {
      return job.value.status as StepState;
    }

    const progress = job.value?.progress?.steps?.[step];
    if (
      job.value &&
      ['completed', 'failed', 'cancelled', 'interrupted'].includes(job.value.status) &&
      progress &&
      ['running', 'cancelling'].includes(progress)
    ) {
      return job.value.status as StepState;
    }
    if (progress && progress !== 'pending') {
      return progress as StepState;
    }
    if (job.value?.operation === step) {
      return job.value.status as StepState;
    }

    if (
      (step === 'import' && project.value.source) ||
      (step === 'transcribe' && project.value.has_transcript) ||
      (step === 'analyze' && project.value.has_analysis) ||
      (step === 'render' && hasCuts.value)
    ) {
      return 'completed';
    }

    return 'pending';
  }

  const stepStates = computed<Record<StepId, StepState>>(() => {
    const map = {} as Record<StepId, StepState>;
    for (const [id] of PIPELINE_STEPS) {
      map[id] = calculateState(id);
    }
    return map;
  });

  const completedCount = computed(() => {
    return Object.values(stepStates.value).filter(s => s === 'completed').length;
  });

  return {
    stepStates,
    completedCount,
    getStepState: (id: StepId) => stepStates.value[id] || 'pending',
  };
}
