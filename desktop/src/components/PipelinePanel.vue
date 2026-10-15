<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue';
import { notify, notifyJob } from '../notifications';
import { analysisLabels } from '../format';
import {
  usePipelinePresentation,
  type PipelineAction,
  type PipelineInput,
} from '../composables/usePipelinePresentation';
import PipelineStatusHero from './pipeline/PipelineStatusHero.vue';
import PipelineStepList from './pipeline/PipelineStepList.vue';
import TechnicalDetails from './ui/TechnicalDetails.vue';
import { vRecoverMedia } from '../directives/recoverMedia';

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
const detailsOpen = ref(false);
const sourcePlayer = ref<HTMLVideoElement>();
watch(
  job,
  value => {
    if (value && ['failed', 'interrupted'].includes(value.status)) notifyJob(value);
  },
  { immediate: true }
);
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
  if (job.value && ['failed', 'interrupted', 'cancelled'].includes(job.value.status))
    notifyJob(job.value, true);
  else notify.error(hero.value.notice || props.project.error?.message || lastFailureReason.value);
}
function releaseSource() {
  const video = sourcePlayer.value;
  if (!video) return;
  video.pause();
  video.removeAttribute('src');
  video.load();
}
watch(
  detailsOpen,
  open => {
    if (!open) releaseSource();
  },
  { flush: 'sync' }
);
onBeforeUnmount(releaseSource);
</script>

<template>
  <section
    class="pipeline-panel preparation-panel"
    aria-label="Central de acompanhamento do projeto"
  >
    <PipelineStatusHero :status="hero" @action="perform" @error-details="errorDetails" />
    <PipelineStepList :steps="overviewSteps" />
    <TechnicalDetails v-model="detailsOpen" title="Detalhes do processamento">
      <dl v-if="job || analysis" class="pipeline-diagnostics">
        <template v-if="job">
          <dt>Tarefa</dt>
          <dd>{{ job.id }}</dd>
          <dt>Operação</dt>
          <dd>{{ job.operation }}</dd>
          <dt v-if="job.stage || job.progress?.stage">Etapa técnica</dt>
          <dd v-if="job.stage || job.progress?.stage">{{ job.stage || job.progress?.stage }}</dd>
        </template>
        <dt v-if="analysis">Análise</dt>
        <dd v-if="analysis">
          <span class="analysis-state">{{ analysisLabels[analysis.state] }}</span> ·
          {{ analysis.completed_windows }}/{{ analysis.total_windows }} janelas ·
          {{ analysis.proposals.length }} propostas
        </dd>
      </dl>
      <PipelineStepList :steps="technicalSteps" technical @action="perform" />
      <figure class="pipeline-video">
        <video
          v-if="detailsOpen && sourceUrl"
          ref="sourcePlayer"
          v-recover-media="sourceUrl"
          :src="sourceUrl"
          controls
          preload="metadata"
          playsinline
          aria-label="Vídeo original"
        />
        <p v-else-if="!sourceUrl">
          {{ project.source ? 'Vídeo indisponível' : 'Vídeo ainda não importado' }}
        </p>
        <figcaption>
          Vídeo original · {{ project.source ? 'Fonte preservada' : 'Aguardando fonte' }}
        </figcaption>
      </figure>
    </TechnicalDetails>
  </section>
</template>

<style scoped>
.preparation-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-width: 0;
  padding: 24px;
  background: transparent;
}
.preparation-panel > :deep(.pipeline-step-list) {
  max-width: 760px;
}
.pipeline-diagnostics {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 8px 16px;
  margin: 0;
  font-size: var(--font-size-control);
}
dt {
  color: var(--color-text-secondary);
}
dd {
  margin: 0;
  overflow-wrap: anywhere;
}
.pipeline-video {
  width: min(100%, 560px);
  margin: 0;
}
.pipeline-video video {
  display: block;
  width: 100%;
  max-height: 320px;
  aspect-ratio: 16/9;
  background: var(--color-canvas);
}
.pipeline-video figcaption {
  margin-top: 8px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-meta);
}
@media (max-width: 1000px) {
  .preparation-panel {
    padding: 16px;
  }
}
</style>
