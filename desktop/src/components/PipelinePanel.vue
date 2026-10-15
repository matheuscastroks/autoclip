<script setup lang="ts">
import AppButton from './AppButton.vue';
import { computed, watch, toRef } from 'vue';
import {
  Check,
  Square,
  RotateCcw,
  LoaderCircle,
  AlertCircle,
  Play,
  Sparkles,
  Scissors,
  Download,
  Film,
  ListOrdered,
  ChevronDown,
  FolderOpen,
} from '@lucide/vue';
import type { Project, Job, Revision, AnalysisView } from '../types';
import { active, labels, analysisLabels, latestJob } from '../format';
import { notifyJob, notify } from '../notifications';
import { usePipelineSteps, type StepId } from '../composables/usePipelineSteps';
import { useRenderFailures } from '../composables/useRenderFailures';

const props = defineProps<{
  project: Project;
  jobs: Job[];
  busy: boolean;
  hasCuts: boolean;
  revisions?: Revision[];
  analysis?: AnalysisView | null;
  sourceUrl?: string;
  selectedCount?: number;
  selectedCandidateIds?: string[];
}>();
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

const names = [
  ['import', 'Importar'],
  ['transcribe', 'Transcrever'],
  ['analyze', 'Analisar'],
  ['choose', 'Selecionar'],
  ['render', 'Gerar'],
  ['export', 'Exportar'],
] as const;
const job = computed(() => latestJob(props.jobs));
const recovery = computed(
  () => job.value && ['failed', 'cancelled', 'interrupted'].includes(job.value.status)
);
const importRecovery = computed(
  () =>
    recovery.value &&
    !props.project.source &&
    ['prepare', 'import'].includes(job.value?.operation || '')
);
const approved = computed(() =>
  props.revisions?.some(r => r.technical_pass && r.review_status === 'approved')
);
const pendingSelectedCount = computed(() =>
  props.selectedCandidateIds
    ? props.selectedCandidateIds.filter(
        id =>
          !props.revisions?.some(
            r => r.candidate_id === id && (r.preview?.state === 'available' || r.technical_pass)
          )
      ).length
    : props.hasCuts
      ? 0
      : props.selectedCount || 0
);
const needsFinalReview = computed(() =>
  props.revisions?.some(
    r => r.technical_pass && ['needs_review', 'stale_review'].includes(r.review_status)
  )
);
const hasPreviews = computed(() =>
  props.revisions?.some(r => r.preview?.state === 'available' && !r.technical_pass)
);
const processing = computed(() => props.jobs.some(j => active(j.status)));

watch(
  job,
  value => {
    if (value && ['failed', 'interrupted'].includes(value.status)) notifyJob(value);
  },
  { immediate: true }
);

const { getStepState } = usePipelineSteps({
  project: toRef(props, 'project'),
  job,
  revisions: toRef(props, 'revisions'),
  selectedCount: computed(() => props.selectedCount || 0),
  importRecovery,
  hasCuts: toRef(props, 'hasCuts'),
});

function state(step: string) {
  return getStepState(step as StepId);
}

function handleStepClick(id: string) {
  if (id === 'transcribe' && props.project.has_transcript) emit('review');
  else if ((id === 'analyze' || id === 'choose') && props.project.has_analysis) emit('analysis');
  else if ((id === 'render' || id === 'export') && props.hasCuts) emit('review');
}

const { failedRenderItem, pendingQueueCount, hasFailure, lastFailureTitle, lastFailureReason } =
  useRenderFailures(toRef(props, 'jobs'), importRecovery, recovery, job);

const completedStepsCount = computed(
  () => names.filter(([id]) => state(id) === 'completed').length
);

function triggerErrorDetails() {
  if (job.value) notifyJob(job.value, true);
  else if (props.project.error) notify.error(props.project.error.message);
  else notify.error(lastFailureReason.value);
}
</script>

<template>
  <section class="pipeline-panel" aria-label="Central de acompanhamento do projeto">
    <!-- 1. CABEÇALHO COMPACTO DO PROJETO -->
    <header class="project-headline-bar">
      <div class="headline-meta">
        <h2 class="project-main-title">Preparação</h2>
        <p class="project-tags-strip">
          Fonte preservada · Acompanhe o processamento e o próximo passo
        </p>
      </div>

      <div class="headline-actions">
        <AppButton
          v-if="processing && job"
          class="button small secondary cancel-job-btn"
          :disabled="job.status === 'cancelling'"
          @click="$emit('cancel', job.id)"
        >
          <Square :size="12" />Cancelar
        </AppButton>
      </div>
    </header>

    <!-- 2. GRADE DE PREPARAÇÃO: FONTE DO VÍDEO (ESQUERDA) + ESTADO & AÇÃO (DIREITA) -->
    <div class="dashboard-grid">
      <!-- PILAR 1: FONTE E VÍDEO ORIGINAL (COLUNA ESQUERDA) -->
      <aside class="dashboard-side-column">
        <!-- PLAYER COMPACTO DO VÍDEO ORIGINAL -->
        <figure class="pipeline-video">
          <video
            v-if="sourceUrl"
            :src="sourceUrl"
            controls
            preload="metadata"
            playsinline
            aria-label="Vídeo original"
          ></video>
          <div v-else class="pipeline-video-empty">
            {{
              project.source
                ? 'Vídeo indisponível'
                : importRecovery
                  ? 'Importação interrompida'
                  : processing && job?.progress?.steps.import === 'running'
                    ? 'Importando vídeo…'
                    : 'Vídeo ainda não importado'
            }}
          </div>
          <figcaption>
            Vídeo original · {{ project.source ? 'Fonte preservada' : 'Aguardando fonte' }}
          </figcaption>
        </figure>

        <!-- CARTÃO DE MÉTRICAS COMPACTAS -->
        <div class="dashboard-metrics-card">
          <div class="metric-item">
            <span class="metric-label">Trechos selecionados</span>
            <strong class="metric-value">{{ selectedCount || 0 }}</strong>
          </div>

          <div v-if="pendingQueueCount > 0" class="metric-item">
            <span class="metric-label">Pendências na fila</span>
            <strong class="metric-value warning-value">{{ pendingQueueCount }}</strong>
          </div>

          <div class="metric-item">
            <span class="metric-label">Temas identificados</span>
            <strong class="metric-value">{{ analysis?.topic_groups.length || 0 }}</strong>
          </div>

          <div class="metric-item analysis-metric-item">
            <span class="metric-label">{{ analysisLabels[analysis?.state || 'not_started'] }}</span>
            <span class="metric-sub">{{
              analysis
                ? `${analysis.completed_windows}/${analysis.total_windows} janelas · ${analysis.topic_groups.length} temas · ${analysis.proposals.length} propostas`
                : 'Aguardando transcrição'
            }}</span>
          </div>

          <AppButton
            v-if="project.has_analysis"
            type="button"
            class="text-button metrics-action-link"
            @click="$emit('analysis')"
          >
            Ver análise →
          </AppButton>
        </div>
      </aside>

      <!-- PILAR 2 & 3: ESTADO REAL & PRÓXIMA AÇÃO (COLUNA DIREITA) -->
      <section class="dashboard-hero-column">
        <!-- ESTADO 1: ATENÇÃO / FALHA (Última Falha & Ação Contextual de Retomada) -->
        <article v-if="hasFailure" class="state-hero-card attention-mode" data-state="attention">
          <div class="hero-body-text">
            <h3>
              {{ importRecovery ? 'Falha na importação do vídeo' : 'A geração precisa de atenção' }}
            </h3>
            <p>
              {{
                importRecovery
                  ? 'O link foi bloqueado ou o arquivo está inacessível. Escolha uma alternativa para prosseguir.'
                  : 'Uma operação apresentou erro. Os resultados preservados continuam disponíveis.'
              }}
            </p>
          </div>

          <!-- CARD DEDICADO: ÚLTIMA FALHA -->
          <div class="last-failure-card">
            <span class="failure-eyebrow">ÚLTIMA FALHA</span>
            <strong class="failure-title">{{ lastFailureTitle }}</strong>
            <p class="failure-reason">{{ lastFailureReason }}</p>
            <AppButton
              type="button"
              class="text-button failure-details-link"
              data-action="error-details"
              @click="triggerErrorDetails"
            >
              Ver detalhes técnicos
            </AppButton>
          </div>

          <!-- AÇÕES DO ESTADO DE FALHA -->
          <div class="hero-action-buttons">
            <template v-if="importRecovery && job">
              <AppButton
                class="button primary hero-primary-btn"
                data-action="retry-import"
                :disabled="busy || processing"
                @click="$emit('resume', job.id)"
              >
                <RotateCcw :size="15" />Tentar novamente
              </AppButton>
              <AppButton
                class="button secondary"
                data-action="replace-source"
                :disabled="busy || processing"
                @click="$emit('replaceSource', job.id)"
              >
                <FolderOpen :size="15" />Usar arquivo local
              </AppButton>
            </template>
            <template v-else-if="failedRenderItem">
              <AppButton
                class="button primary hero-primary-btn"
                :disabled="busy || processing"
                @click="$emit('resume', failedRenderItem.job.id)"
              >
                <RotateCcw :size="15" />Abrir fila e retomar →
              </AppButton>
              <AppButton class="button secondary" @click="$emit('analysis')">
                Ajustar seleção
              </AppButton>
            </template>
            <template v-else-if="job">
              <AppButton
                class="button primary hero-primary-btn"
                :disabled="busy || processing"
                @click="$emit('resume', job.id)"
              >
                <RotateCcw :size="15" />Retomar processamento
              </AppButton>
            </template>
          </div>
        </article>

        <!-- ESTADO 2: PROCESSAMENTO ATIVO -->
        <article
          v-else-if="processing && job"
          class="state-hero-card processing-mode"
          data-state="processing"
        >
          <div class="hero-body-text">
            <h3>Processamento em andamento</h3>
            <p>Executando etapa atual em segundo plano.</p>
          </div>

          <div class="processing-status-strip">
            <el-progress
              :indeterminate="true"
              :percentage="0"
              :stroke-width="4"
              :show-text="false"
              color="var(--color-text-primary)"
              class="stage-progress indeterminate"
              role="progressbar"
              aria-label="Progresso da tarefa"
            />
            <small>Status: {{ labels[job.status] || job.status }}</small>
          </div>

          <div class="hero-action-buttons">
            <AppButton
              class="button secondary"
              :disabled="job.status === 'cancelling'"
              @click="$emit('cancel', job.id)"
            >
              <Square :size="14" />Cancelar
            </AppButton>
          </div>
        </article>

        <!-- ESTADO 3: PRÓXIMO PASSO NORMAL (Transcrição, Análise, Seleção, Renderização ou Cortes) -->
        <article v-else class="state-hero-card ready-mode" data-state="ready">
          <!-- CASO A: Transcrição Pendente -->
          <template v-if="!project.has_transcript && !hasCuts">
            <div class="hero-body-text">
              <h3>Transcrição pendente</h3>
              <p>Gere a transcrição com marcação temporal para habilitar a curadoria.</p>
            </div>
            <div class="hero-action-buttons">
              <AppButton
                class="button primary hero-primary-btn"
                :disabled="busy || !project.source || processing"
                @click="$emit('transcribe')"
              >
                <Play :size="15" />Transcrever áudio
              </AppButton>
            </div>
          </template>

          <!-- CASO B: Análise Pendente -->
          <template v-else-if="!project.has_analysis && !hasCuts">
            <div class="hero-body-text">
              <h3>Análise pendente</h3>
              <p>
                Analise o conteúdo transcrito ({{ project.word_count.toLocaleString('pt-BR') }}
                palavras) para descobrir os melhores cortes.
              </p>
            </div>
            <div class="hero-action-buttons">
              <AppButton
                class="button primary hero-primary-btn"
                :disabled="busy || processing"
                @click="$emit('analyze')"
              >
                <Sparkles :size="15" />Iniciar análise
              </AppButton>
            </div>
          </template>

          <!-- CASO C: Seleção Pendente -->
          <template v-else-if="!hasCuts && (!selectedCount || selectedCount === 0)">
            <div class="hero-body-text">
              <h3>Curadoria de cortes disponível</h3>
              <p>
                {{ analysis?.proposals.length || 0 }} propostas e
                {{ analysis?.topic_groups.length || 0 }} temas identificados.
              </p>
            </div>
            <div class="hero-action-buttons">
              <AppButton
                class="button primary hero-primary-btn"
                :disabled="busy"
                @click="$emit('analysis')"
              >
                <Scissors :size="15" />Selecionar cortes
              </AppButton>
            </div>
          </template>

          <!-- CASO D: Pronto para Renderizar Cortes -->
          <template v-else-if="pendingSelectedCount > 0">
            <div class="hero-body-text">
              <h3>{{ pendingSelectedCount }} proposta(s) aguardando prévia</h3>
              <p>Gere as prévias verticais 9:16 com enquadramento e legendas.</p>
            </div>
            <div class="hero-action-buttons">
              <AppButton
                class="button primary hero-primary-btn"
                :disabled="busy || !selectedCount || !project.has_analysis"
                @click="$emit('generate')"
              >
                <Film :size="15" />Gerar prévias rápidas
              </AppButton>
              <AppButton class="button secondary" @click="$emit('analysis')">
                Ajustar seleção
              </AppButton>
            </div>
          </template>

          <!-- CASO E: Cortes Prontos para Revisão / Exportação -->
          <template v-else>
            <div class="hero-body-text">
              <h3>
                {{
                  needsFinalReview
                    ? 'Versões finais para revisar'
                    : approved
                      ? 'Cortes aprovados para exportar'
                      : hasPreviews
                        ? 'Prévias prontas para avaliar'
                        : 'Acompanhe seus cortes'
                }}
              </h3>
              <p>
                {{
                  needsFinalReview
                    ? 'Confira o vídeo final e os cinco critérios editoriais antes de aprovar.'
                    : approved
                      ? 'A exportação inclui somente versões finais tecnicamente válidas e aprovadas.'
                      : hasPreviews
                        ? 'Avalie as prévias em Cortes. Gere a versão final apenas dos resultados que quiser publicar.'
                        : 'Abra Cortes para verificar versões, avisos e ações disponíveis.'
                }}
              </p>
            </div>
            <div class="hero-action-buttons">
              <AppButton
                v-if="approved && !needsFinalReview"
                class="button primary hero-primary-btn"
                :disabled="busy"
                @click="$emit('export')"
              >
                <Download :size="15" />Exportar aprovados
              </AppButton>
              <AppButton v-else class="button primary hero-primary-btn" @click="$emit('review')">
                <Play :size="15" />{{
                  needsFinalReview
                    ? 'Revisar versões finais'
                    : hasPreviews
                      ? 'Avaliar prévias'
                      : 'Abrir cortes'
                }}
              </AppButton>
              <AppButton
                v-if="approved && !needsFinalReview"
                class="button secondary"
                @click="$emit('review')"
              >
                Abrir cortes
              </AppButton>
              <AppButton
                v-if="approved && needsFinalReview"
                class="button secondary"
                :disabled="busy"
                @click="$emit('export')"
              >
                <Download :size="15" />Exportar aprovados
              </AppButton>
            </div>
          </template>
        </article>
      </section>
    </div>

    <!-- 4. HISTÓRICO TÉCNICO DAS 6 ETAPAS (GAVETA EXPANSÍVEL DISCRETA NO RODAPÉ) -->
    <!-- Preserva os seletores [data-stage], .stage-progress e botões de recuperação de forma limpa -->
    <details class="technical-history-disclosure">
      <summary class="technical-history-trigger">
        <ListOrdered :size="15" />
        <span>Detalhes do processamento</span>
        <ChevronDown :size="14" class="disclosure-chevron" />
      </summary>

      <div class="technical-history-content">
        <!-- ESTEIRA LINEAR DE PROCESSAMENTO -->
        <section class="stepper-track-wrap" aria-label="Esteira de progresso das etapas">
          <div class="stepper-track-title">
            <strong>Esteira de Processamento</strong>
            <span>{{ completedStepsCount }} de {{ names.length }} etapas concluídas</span>
          </div>
          <div class="stepper-track">
            <template v-for="([id, title], idx) in names" :key="id">
              <div
                class="stepper-node"
                :data-stepper-stage="id"
                :data-state="state(id)"
                :class="{ clickable: state(id) === 'completed' }"
                role="button"
                :tabindex="state(id) === 'completed' ? 0 : -1"
                @click="handleStepClick(id)"
              >
                <div class="node-circle">
                  <Check v-if="state(id) === 'completed'" :size="14" />
                  <LoaderCircle
                    v-else-if="['running', 'cancelling', 'processing'].includes(state(id))"
                    class="spin"
                    :size="14"
                  />
                  <AlertCircle
                    v-else-if="['failed', 'cancelled', 'interrupted'].includes(state(id))"
                    :size="14"
                  />
                  <span v-else>{{ idx + 1 }}</span>
                </div>
                <span class="node-label">{{ title }}</span>
                <small class="node-subtext">{{
                  state(id) === 'waiting' ? 'Próxima' : labels[state(id)] || state(id)
                }}</small>
              </div>
              <div
                v-if="idx < names.length - 1"
                class="stepper-connector"
                :class="{ done: state(id) === 'completed' }"
              ></div>
            </template>
          </div>
        </section>

        <ol class="technical-steps-list">
          <li
            v-for="[id, title] in names"
            :key="id"
            class="technical-step-row"
            :data-stage="id"
            :data-state="state(id)"
          >
            <span class="step-mark" :class="{ done: state(id) === 'completed' }">
              <Check v-if="state(id) === 'completed'" :size="14" />
              <span v-else>{{ names.findIndex(n => n[0] === id) + 1 }}</span>
            </span>

            <div class="step-info-col">
              <div class="step-header-line">
                <strong>{{ title }}</strong>
                <span class="step-state-badge">{{
                  state(id) === 'waiting' ? 'Próxima ação' : labels[state(id)] || state(id)
                }}</span>
              </div>

              <div
                v-if="!['pending', 'waiting'].includes(state(id))"
                role="progressbar"
                :aria-label="title"
                :aria-valuenow="state(id) === 'completed' ? 100 : undefined"
                aria-valuemin="0"
                aria-valuemax="100"
                class="stage-progress"
                :class="{
                  indeterminate: ['running', 'processing', 'cancelling'].includes(state(id)),
                  complete: state(id) === 'completed',
                  failed: ['failed', 'cancelled', 'interrupted'].includes(state(id)),
                }"
              >
                <span></span>
              </div>

              <!-- Ações técnicas específicas por etapa para compatibilidade com testes -->
              <div v-if="id === 'import' && importRecovery && job" class="import-recovery-actions">
                <AppButton
                  v-if="job.error"
                  type="button"
                  class="text-button"
                  data-action="error-details"
                  @click="notifyJob(job, true)"
                  >Ver motivo da falha</AppButton
                >
                <div class="recovery-btn-row">
                  <AppButton
                    class="button small primary"
                    data-action="retry-import"
                    :disabled="busy || processing"
                    @click="$emit('resume', job.id)"
                    ><RotateCcw :size="13" />Tentar novamente</AppButton
                  >
                  <AppButton
                    class="button small secondary"
                    data-action="replace-source"
                    :disabled="busy || processing"
                    @click="$emit('replaceSource', job.id)"
                    >Usar arquivo local</AppButton
                  >
                </div>
              </div>

              <div class="technical-step-actions">
                <AppButton
                  v-if="
                    id === 'transcribe' &&
                    !project.has_transcript &&
                    !project.is_manual &&
                    !processing
                  "
                  class="button small secondary"
                  :disabled="busy || !project.source"
                  @click="$emit('transcribe')"
                  >Transcrever vídeo</AppButton
                >
                <AppButton
                  v-if="
                    id === 'analyze' && !project.is_manual && !processing && project.has_transcript
                  "
                  class="button small secondary"
                  :disabled="busy"
                  @click="$emit('analyze')"
                  >{{
                    project.has_analysis
                      ? 'Nova análise'
                      : recovery
                        ? 'Continuar análise'
                        : 'Iniciar análise'
                  }}</AppButton
                >
                <AppButton
                  v-if="id === 'choose' && !project.is_manual"
                  class="button small secondary"
                  :disabled="busy || !project.has_analysis"
                  @click="$emit('render')"
                  >{{
                    selectedCount
                      ? selectedCount + ' trechos selecionados · Ajustar'
                      : 'Escolher trechos'
                  }}</AppButton
                >
                <AppButton
                  v-if="id === 'render' && !project.is_manual"
                  class="button small primary"
                  :disabled="busy || !selectedCount || !project.has_analysis"
                  @click="$emit('generate')"
                  >Gerar prévias rápidas</AppButton
                >
                <AppButton
                  v-if="id === 'export' && approved"
                  class="button small primary"
                  :disabled="busy"
                  @click="$emit('export')"
                  >Exportar aprovados</AppButton
                >
              </div>
            </div>
          </li>
        </ol>
      </div>
    </details>
  </section>
</template>

<style scoped>
.pipeline-panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* 1. Headline do Projeto */
.project-headline-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding-bottom: 4px;
}

.headline-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.project-section-eyebrow {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 2px;
}

.project-main-title {
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--color-text-primary, #f2f4f7);
  margin: 0;
  line-height: 1.25;
}

.project-tags-strip {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.82rem;
  color: var(--color-text-muted, #a0abba);
  margin: 0;
}

.source-author {
  color: var(--color-text-secondary, #cbd5e1);
  font-weight: 500;
}

.meta-dot {
  opacity: 0.5;
}

/* 2. Esteira Linear de Processamento */
.stepper-track-wrap {
  background: var(--color-surface, #16181b);
  border: 1px solid var(--color-border-subtle, #2e3644);
  border-radius: var(--radius-panel, 8px);
  padding: 14px 18px;
  margin-bottom: 16px;
}

.stepper-track-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.stepper-track-title strong {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--color-text-primary, #f2f4f7);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stepper-track-title span {
  font-size: 0.78rem;
  color: var(--color-text-muted, #a0abba);
}

.stepper-track {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  gap: 6px;
}

.stepper-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  position: relative;
  z-index: 2;
  min-width: 60px;
}

.stepper-node.clickable {
  cursor: pointer;
}

.node-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-canvas, #0e1013);
  border: 1.5px solid var(--color-border-subtle, #2e3644);
  color: var(--color-text-muted, #a0abba);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  transition: all 0.2s ease;
}

.stepper-node[data-state='completed'] .node-circle {
  background: rgba(16, 185, 129, 0.16);
  border-color: rgba(16, 185, 129, 0.45);
  color: #34d399;
}

.stepper-node[data-state='running'] .node-circle,
.stepper-node[data-state='processing'] .node-circle {
  background: var(--color-surface-selected);
  border-color: var(--color-border-strong);
  color: var(--color-text-primary);
}

.stepper-node[data-state='failed'] .node-circle,
.stepper-node[data-state='interrupted'] .node-circle {
  background: rgba(239, 68, 68, 0.16);
  border-color: rgba(239, 68, 68, 0.45);
  color: #f87171;
}

.stepper-node[data-state='waiting'] .node-circle {
  border-color: var(--color-border-strong);
  color: var(--color-text-primary);
}

.node-label {
  font-size: 0.76rem;
  font-weight: 600;
  color: var(--color-text-primary, #f2f4f7);
}

.node-subtext {
  font-size: 0.68rem;
  color: var(--color-text-muted, #a0abba);
}

.stepper-connector {
  flex: 1;
  height: 2px;
  background: var(--color-border-subtle, #2e3644);
  margin-top: -18px;
  transition: background 0.2s ease;
}

.stepper-connector.done {
  background: #10b981;
}

/* 3. Grade do Dashboard */
.dashboard-grid {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}

/* Coluna Principal: Hero de Estado */
.dashboard-hero-column {
  display: flex;
  flex-direction: column;
}

.state-hero-card {
  background: transparent;
  border: none;
  border-left: 3px solid var(--color-border-strong);
  border-radius: 0;
  padding: 12px 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.state-hero-card.attention-mode {
  background: rgba(239, 68, 68, 0.04);
  border: none;
  border-left: 3px solid #ef4444;
  border-radius: 0 8px 8px 0;
}

.state-hero-card.processing-mode {
  background: var(--color-surface-selected);
  border: none;
  border-left: 3px solid var(--color-border-strong);
  border-radius: 0 8px 8px 0;
}

.state-hero-card.ready-mode {
  background: transparent;
  border: none;
  border-left: 3px solid var(--color-border-strong);
  border-radius: 0;
}

.hero-header-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 3px 10px;
  border-radius: 999px;
  width: fit-content;
}

.hero-header-badge.attention-badge {
  background: rgba(239, 68, 68, 0.16);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.35);
}

.hero-header-badge.processing-badge {
  background: var(--color-surface-selected);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-subtle);
}

.hero-header-badge.ready-badge {
  background: var(--color-surface-selected);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-subtle);
}

.hero-body-text h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text-primary, #f2f4f7);
  margin: 0 0 6px;
  line-height: 1.3;
}

.hero-body-text p {
  font-size: 0.88rem;
  color: var(--color-text-secondary, #cbd5e1);
  margin: 0;
  line-height: 1.5;
  max-width: 65ch;
}

/* Card Dedicado: Última Falha */
.last-failure-card {
  background: rgba(239, 68, 68, 0.06);
  border: none;
  border-left: 2px solid rgba(239, 68, 68, 0.6);
  border-radius: 0 6px 6px 0;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.failure-eyebrow {
  font-size: 0.68rem;
  font-weight: 700;
  color: #f87171;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.failure-title {
  font-size: 0.95rem;
  color: var(--color-text-primary, #f2f4f7);
  font-weight: 600;
}

.failure-reason {
  font-size: 0.82rem;
  color: var(--color-text-muted, #a0abba);
  margin: 0;
}

.failure-details-link {
  font-size: 0.78rem;
  color: var(--color-text-primary);
  margin-top: 4px;
  padding: 0;
  text-decoration: underline;
  cursor: pointer;
  align-self: flex-start;
}

/* Botões de Ação do Hero */
.hero-action-buttons {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 4px;
}

.hero-primary-btn {
  font-weight: 600;
  padding: 10px 20px;
  font-size: 0.9rem;
}

.processing-status-strip {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.processing-status-strip small {
  font-size: 0.75rem;
  color: var(--color-text-muted, #a0abba);
}

/* Coluna Lateral: Vídeo Original + Métricas */
.dashboard-side-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.pipeline-video {
  margin: 0;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--color-border-subtle, #2e3644);
  background: #000;
  display: flex;
  flex-direction: column;
}

.pipeline-video video {
  width: 100%;
  aspect-ratio: 16/9;
  display: block;
  object-fit: cover;
}

.pipeline-video-empty {
  width: 100%;
  aspect-ratio: 16/9;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  text-align: center;
  font-size: 0.8rem;
  color: var(--color-text-muted, #a0abba);
  background: var(--color-surface, #16191f);
}

.pipeline-video figcaption {
  font-size: 0.72rem;
  padding: 6px 12px;
  background: var(--color-surface, #16191f);
  color: var(--color-text-muted, #a0abba);
  border-top: 1px solid var(--color-border-subtle, #2e3644);
}

.dashboard-metrics-card {
  background: transparent;
  border: none;
  border-radius: 0;
  padding: 4px 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.82rem;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--color-border-subtle, #2e3644);
}

.metric-item:last-of-type {
  border-bottom: none;
  padding-bottom: 0;
}

.metric-label {
  color: var(--color-text-muted, #a0abba);
}

.metric-value {
  color: var(--color-text-primary, #f2f4f7);
  font-weight: 600;
}

.metric-value.warning-value {
  color: var(--color-text-primary);
  background: var(--color-surface-selected);
  padding: 1px 8px;
  border-radius: 6px;
}

.analysis-metric-item {
  flex-direction: column;
  align-items: flex-start;
  gap: 3px;
}

.metric-sub {
  font-size: 0.76rem;
  color: var(--color-text-secondary, #cbd5e1);
  line-height: 1.35;
}

.metrics-action-link {
  font-size: 0.78rem;
  color: var(--color-text-primary);
  padding: 2px 0 0;
  text-align: left;
  font-weight: 600;
  cursor: pointer;
}

/* 4. Gaveta de Histórico Técnico (Discreta e Expansível) */
.technical-history-disclosure {
  background: transparent;
  border: none;
  border-top: 1px solid var(--color-border-subtle, #2e3644);
  border-radius: 0;
  overflow: hidden;
  margin-top: 12px;
}

.technical-history-trigger {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 0;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-text-muted, #a0abba);
  cursor: pointer;
  user-select: none;
  background: transparent;
  transition: all 0.15s ease;
}

.technical-history-trigger:hover {
  color: var(--color-text-primary, #f2f4f7);
  background: transparent;
}

.disclosure-chevron {
  margin-left: auto;
  transition: transform 0.2s ease;
}

.technical-history-disclosure[open] .disclosure-chevron {
  transform: rotate(180deg);
}

.technical-history-content {
  padding: 10px 0 0;
  border-top: none;
}

.technical-steps-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.technical-step-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 8px 0;
  border-radius: 0;
  background: transparent;
  border: none;
  border-bottom: 1px solid var(--color-border-subtle, #2e3644);
}

.step-mark {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-canvas, #0e1013);
  border: 1px solid var(--color-border-subtle, #2e3644);
  color: var(--color-text-muted, #a0abba);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.72rem;
  font-weight: 700;
  flex-shrink: 0;
  margin-top: 2px;
}

.step-mark.done {
  background: rgba(16, 185, 129, 0.16);
  border-color: rgba(16, 185, 129, 0.4);
  color: #34d399;
}

.step-info-col {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.step-header-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.step-header-line strong {
  font-size: 0.82rem;
  color: var(--color-text-primary, #f2f4f7);
}

.step-state-badge {
  font-size: 0.72rem;
  color: var(--color-text-muted, #a0abba);
}

.import-recovery-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 4px;
}

.recovery-btn-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.export-step-action {
  margin-top: 4px;
}

@media (max-width: 900px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
</style>
