<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { notify, notifyJob } from '../notifications';
import { analysisLabels, labels, stages, time } from '../format';
import {
  usePipelinePresentation,
  type PipelineAction,
  type PipelineInput,
} from '../composables/usePipelinePresentation';
import PipelineStatusHero from './pipeline/PipelineStatusHero.vue';
import PipelineStepList from './pipeline/PipelineStepList.vue';
import AppIcon from './ui/AppIcon.vue';

const props = defineProps<PipelineInput & { sourceUrl?: string }>();
const emit = defineEmits<{
  transcribe: [];
  analyze: [];
  render: [];
  analysis: [];
  review: [];
  cancel: [id: string];
  resume: [id: string];
  replaceSource: [id: string];
  generate: [];
  export: [];
}>();
const { job, hero, overviewSteps, technicalSteps, lastFailureReason } =
  usePipelinePresentation(props);
const asidePanel = ref<HTMLElement | null>(null);

watch(
  job,
  value => {
    if (value && ['failed', 'interrupted'].includes(value.status)) notifyJob(value);
  },
  { immediate: true }
);

const technicalStatusBadge = computed(() => {
  if (job.value) {
    if (['running', 'cancelling'].includes(job.value.status)) {
      return { text: 'Em execução', type: 'active' as const };
    }
    if (job.value.status === 'failed') {
      return { text: 'Falha técnica', type: 'error' as const };
    }
    if (job.value.status === 'completed') {
      return { text: 'Concluído', type: 'success' as const };
    }
  }
  if (props.analysis?.state === 'running') {
    return { text: 'Analisando', type: 'active' as const };
  }
  const completedCount = technicalSteps.value.filter(s => s.state === 'completed').length;
  return {
    text: `${completedCount}/${technicalSteps.value.length} etapas`,
    type: 'default' as const,
  };
});

const overviewCompletedCount = computed(
  () => overviewSteps.value.filter(s => s.state === 'completed').length
);

const technicalCompletedCount = computed(
  () => technicalSteps.value.filter(s => s.state === 'completed').length
);

const currentStageLabel = computed(() => {
  const stageKey = job.value?.stage || job.value?.progress?.stage;
  if (!stageKey) return null;
  return stages[stageKey] || stageKey;
});

const currentOperationLabel = computed(() => {
  if (!job.value?.operation) return null;
  const op = job.value.operation;
  return stages[op] || labels[op] || op;
});

function perform(action: PipelineAction) {
  if (action.disabled) return;
  switch (action.id) {
    case 'cancel':
      if (action.jobId) emit('cancel', action.jobId);
      break;
    case 'resume':
      if (action.jobId) emit('resume', action.jobId);
      break;
    case 'replaceSource':
      if (action.jobId) emit('replaceSource', action.jobId);
      break;
    case 'transcribe':
      emit('transcribe');
      break;
    case 'analyze':
      emit('analyze');
      break;
    case 'analysis':
      emit('analysis');
      break;
    case 'review':
      emit('review');
      break;
    case 'generate':
      emit('generate');
      break;
    case 'export':
      emit('export');
      break;
  }
}

function errorDetails() {
  if (job.value) {
    notifyJob(job.value, true);
  } else if (lastFailureReason.value) {
    notify.error(lastFailureReason.value, { force: true });
  }
  if (asidePanel.value && typeof asidePanel.value.scrollIntoView === 'function') {
    asidePanel.value.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}
</script>

<template>
  <section
    class="pipeline-panel preparation-panel preparation-dashboard"
    data-component="pipeline-panel"
    :data-status="project.status"
    :data-job-status="job?.status"
  >
    <!-- Coluna Principal (Ações e Fluxo Editorial) -->
    <div class="pipeline-main dashboard-column">
      <!-- Card 1: Herói de Status e Ação Primária -->
      <PipelineStatusHero :status="hero" @action="perform" @error-details="errorDetails" />

      <!-- Subgrid: Etapas do Fluxo e Telemetria de Processamento Lado a Lado -->
      <div class="pipeline-subgrid">
        <!-- Card 2: Etapas do Fluxo (Milestones do Projeto) -->
        <section class="dashboard-card milestones-card" aria-labelledby="milestones-heading">
          <header class="card-header">
            <div class="card-header-left">
              <AppIcon name="queue" size="sm" class="card-icon" />
              <h3 id="milestones-heading" class="card-title">Etapas do Fluxo</h3>
            </div>
            <span class="card-badge">
              {{ overviewCompletedCount }} de {{ overviewSteps.length }}
            </span>
          </header>
          <div class="card-body milestones-body">
            <PipelineStepList :steps="overviewSteps" @action="perform" />
          </div>
        </section>

        <!-- Card 3: Telemetria de Processamento -->
        <section class="dashboard-card telemetry-card technical-details" data-component="processing-details">
          <header class="card-header">
            <div class="card-header-left">
              <AppIcon name="cpu" size="sm" class="card-icon" />
              <h3 class="card-title">Telemetria</h3>
            </div>
            <span class="status-badge" :class="technicalStatusBadge.type">
              <span v-if="technicalStatusBadge.type === 'active'" class="status-indicator-dot" />
              {{ technicalStatusBadge.text }}
            </span>
          </header>

          <div class="card-body">
            <dl v-if="job || analysis" class="pipeline-diagnostics">
              <!-- Tarefa ativa -->
              <div v-if="job" class="diagnostic-row">
                <dt class="diagnostic-label">
                  <span class="indicator-dot active" />
                  Tarefa
                </dt>
                <dd class="diagnostic-value">
                  <code class="job-id-code" :title="job.id">{{ job.id }}</code>
                </dd>
              </div>

              <!-- Operação -->
              <div v-if="currentOperationLabel" class="diagnostic-row">
                <dt class="diagnostic-label">Operação</dt>
                <dd class="diagnostic-value">
                  <span class="operation-pill">{{ currentOperationLabel }}</span>
                </dd>
              </div>

              <!-- Etapa técnica -->
              <div v-if="currentStageLabel" class="diagnostic-row">
                <dt class="diagnostic-label">Etapa técnica</dt>
                <dd class="diagnostic-value">
                  <span class="stage-tag">{{ currentStageLabel }}</span>
                </dd>
              </div>

              <!-- Diagnóstico da Análise -->
              <div v-if="analysis" class="diagnostic-row diagnostic-row--analysis">
                <dt class="diagnostic-label">
                  <span
                    class="indicator-dot"
                    :class="analysis.state === 'running' ? 'active' : 'subtle'"
                  />
                  Análise de Conteúdo
                </dt>
                <dd class="diagnostic-value diagnostic-value--analysis">
                  <div class="analysis-status-badge">
                    <span class="analysis-state" :data-state="analysis.state">
                      {{ analysisLabels[analysis.state] }}
                    </span>
                  </div>
                  <div class="analysis-chips">
                    <span class="telemetry-chip">
                      <svg
                        width="12"
                        height="12"
                        viewBox="0 0 16 16"
                        fill="currentColor"
                        aria-hidden="true"
                      >
                        <path
                          d="M2 3.5A1.5 1.5 0 0 1 3.5 2h9A1.5 1.5 0 0 1 14 3.5v9a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 2 12.5v-9zM3.5 3a.5.5 0 0 0-.5.5V6h10V3.5a.5.5 0 0 0-.5-.5h-9zM13 7H3v5.5a.5.5 0 0 0 .5.5h9a.5.5 0 0 0 .5-.5V7z"
                        />
                      </svg>
                      {{ analysis.completed_windows }}/{{ analysis.total_windows }} janelas
                    </span>
                    <span class="telemetry-chip">
                      <svg
                        width="12"
                        height="12"
                        viewBox="0 0 16 16"
                        fill="currentColor"
                        aria-hidden="true"
                      >
                        <path
                          d="M4 4.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0zm0 7a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0zm4.5-3.5L5.7 6.2a2.5 2.5 0 0 0-3.2-1.2 2.5 2.5 0 0 0-1.2 3.2l7.2 4.3 6-3.6-6-3.6z"
                        />
                      </svg>
                      {{ analysis.proposals.length }} propostas
                    </span>
                  </div>
                </dd>
              </div>
            </dl>

            <div v-else class="project-specs-grid">
              <div class="spec-row">
                <span class="spec-label">Duração da mídia</span>
                <span class="spec-value">{{ project.duration_us ? time(project.duration_us) : '—' }}</span>
              </div>
              <div class="spec-row">
                <span class="spec-label">Transcrição</span>
                <span class="spec-value">{{ project.word_count ? `${project.word_count} palavras` : (project.has_transcript ? 'Concluída' : 'Aguardando') }}</span>
              </div>
              <div class="spec-row">
                <span class="spec-label">Cortes sugeridos</span>
                <span class="spec-value">{{ project.has_analysis ? 'Disponíveis' : 'Aguardando' }}</span>
              </div>
              <div class="spec-row">
                <span class="spec-label">Motor local</span>
                <span class="spec-value spec-value--status">
                  <span class="indicator-dot subtle" />
                  Pronto para tarefas
                </span>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>

    <!-- Coluna Lateral (Fases do Motor Local ocupando toda a coluna da direita) -->
    <aside ref="asidePanel" class="pipeline-aside dashboard-column" aria-label="Detalhes do processamento">
      <!-- Card 4: Fases do Motor Local (Ocupa toda a coluna da direita) -->
      <section class="dashboard-card stages-card full-column-card" aria-labelledby="stages-heading">
        <header class="card-header">
          <div class="card-header-left">
            <AppIcon name="engine" size="sm" class="card-icon" />
            <h3 id="stages-heading" class="card-title">Fases do Motor Local</h3>
          </div>
          <span class="card-badge">
            {{ technicalCompletedCount }}/{{ technicalSteps.length }} etapas
          </span>
        </header>

        <div class="card-body stages-body">
          <PipelineStepList :steps="technicalSteps" technical @action="perform" />
        </div>
      </section>
    </aside>
  </section>
</template>

<style scoped>
.preparation-dashboard {
  display: grid;
  grid-template-columns: minmax(0, 1.75fr) minmax(320px, 1fr);
  gap: 16px;
  align-items: start;
  min-width: 0;
  padding: 0 0 24px 0;
  background: transparent;
  border: none;
  box-shadow: none;
  border-radius: 0;
}

.dashboard-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.pipeline-subgrid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 16px;
  align-items: stretch;
}

.pipeline-aside {
  position: sticky;
  top: 16px;
}

.full-column-card {
  height: 100%;
}

/* Modular Dashboard Cards */
.dashboard-card {
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
  overflow: hidden;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.dashboard-card:hover {
  border-color: var(--color-border-strong);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border-subtle);
}

.card-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-icon {
  color: var(--color-action-primary);
  opacity: 0.9;
}

.card-title {
  font-size: var(--font-size-control);
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
  letter-spacing: -0.01em;
}

.card-badge {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-muted);
  background: var(--color-surface-raised);
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid var(--color-border-subtle);
}

.card-body {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.milestones-body,
.stages-body {
  padding: 10px 12px;
}

/* Status Badges */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 500;
  border-radius: 999px;
  line-height: 1.3;
}

.status-badge.default {
  background: var(--color-surface-raised);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-subtle);
}

.status-badge.active {
  background: rgba(175, 198, 213, 0.12);
  color: var(--color-action-primary);
  border: 1px solid rgba(175, 198, 213, 0.3);
}

.status-badge.success {
  background: var(--color-success-soft);
  color: var(--color-success);
  border: 1px solid var(--color-success-border);
}

.status-badge.error {
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

/* Diagnostics Rows */
.pipeline-diagnostics {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0;
  padding: 0;
}

.diagnostic-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 10px;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-control);
  transition: border-color 0.15s ease;
}

.diagnostic-row:hover {
  border-color: var(--color-border-strong);
}

.diagnostic-row--analysis {
  background: rgba(175, 198, 213, 0.04);
  border-color: rgba(175, 198, 213, 0.2);
}

.diagnostic-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-secondary);
  margin: 0;
}

.indicator-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
}

.indicator-dot.active {
  background-color: var(--color-action-primary);
  box-shadow: 0 0 6px rgba(175, 198, 213, 0.6);
}

.indicator-dot.subtle {
  background-color: var(--color-border-strong);
}

.diagnostic-value {
  margin: 0;
  font-size: var(--font-size-control);
  color: var(--color-text-primary);
  overflow-wrap: anywhere;
}

.job-id-code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 11px;
  color: var(--color-text-primary);
  background: var(--color-canvas);
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid var(--color-border-subtle);
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.operation-pill {
  display: inline-flex;
  align-items: center;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-action-primary);
}

.stage-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
  background: var(--color-surface-hover);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-subtle);
}

.diagnostic-value--analysis {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.analysis-status-badge {
  display: flex;
  align-items: center;
}

.analysis-state {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.analysis-state[data-state='completed'] {
  color: var(--color-success);
}

.analysis-state[data-state='running'] {
  color: var(--color-action-primary);
}

.analysis-state[data-state='failed'] {
  color: var(--color-danger);
}

.analysis-chips {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.telemetry-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: var(--color-text-secondary);
  background: var(--color-canvas);
  padding: 2px 7px;
  border-radius: 4px;
  border: 1px solid var(--color-border-subtle);
}

.project-specs-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.spec-row {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 8px 10px;
  border-radius: var(--radius-control);
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
}

.spec-label {
  font-size: 11px;
  color: var(--color-text-muted);
  font-weight: 500;
}

.spec-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.spec-value--status {
  color: var(--color-text-secondary);
}

.telemetry-idle {
  padding: 12px;
  background: var(--color-surface-raised);
  border: 1px dashed var(--color-border-subtle);
  border-radius: var(--radius-control);
  text-align: center;
}

.idle-text {
  font-size: 12px;
  color: var(--color-text-muted);
}

@media (max-width: 1024px) {
  .preparation-dashboard {
    grid-template-columns: 1fr;
    padding: 16px;
  }
  .pipeline-aside {
    position: static;
  }
}
</style>
