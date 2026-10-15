<script setup lang="ts">
import AppButton from './AppButton.vue';
import { computed, ref, watch } from 'vue';
import { ArrowLeft, FolderOpen, FileText, Scissors, Play, Search, Clock } from '@lucide/vue';
import type {
  Project,
  Transcript,
  Revision,
  Job,
  Decision,
  AnalysisView,
  AnalysisSelection,
} from '../types';
import { time, projectLabel, active } from '../format';
import { notify } from '../notifications';
import ReviewPanel from './ReviewPanel.vue';
import PipelinePanel from './PipelinePanel.vue';
import AnalysisPanel from './AnalysisPanel.vue';
import { vRecoverMedia } from '../directives/recoverMedia';

const props = defineProps<{
  project: Project;
  transcript: Transcript | null;
  revisions: Revision[];
  jobs: Job[];
  sourceUrl: string;
  previewUrl: string;
  busy: boolean;
  selectedRevision?: string;
  mediaLoading?: boolean;
  loadMedia?: (asset: string) => Promise<string>;
  analysis?: AnalysisView | null;
  selection?: AnalysisSelection | null;
}>();
defineEmits<{
  back: [];
  folder: [];
  transcribe: [];
  analyze: [];
  resumeAnalysis: [];
  render: [value: { analysis_hash: string; candidate_ids: string[] }];
  renderFinal: [id: string];
  selection: [value: AnalysisSelection];
  cancel: [id: string];
  resume: [id: string];
  replaceSource: [id: string];
  select: [id: string];
  decision: [value: Decision];
  export: [];
  delete: [id: string];
  deleted: [];
  retry: [value: { job_id: string; candidate_id: string }];
  bulkDelete: [ids: string[]];
  bulkExport: [ids: string[]];
}>();

const tab = ref('overview'),
  player = ref<HTMLVideoElement>();
const transcriptQuery = ref('');
watch(
  () => props.project.warnings,
  values => {
    for (const warning of values)
      notify.warning(warning, { key: 'project:' + props.project.id + ':' + warning });
  },
  { immediate: true }
);

const processing = computed(() => props.jobs.some(j => active(j.status)));
const segments = computed(() =>
  props.transcript?.segments.length
    ? props.transcript.segments
    : props.transcript?.words.reduce<
        { id: string; text: string; start_us: number; end_us: number }[]
      >((all, w, i) => {
        if (i % 12 === 0)
          all.push({ id: w.id, text: w.text, start_us: w.start_us, end_us: w.end_us });
        else {
          all[all.length - 1].text += ' ' + w.text;
          all[all.length - 1].end_us = w.end_us;
        }
        return all;
      }, []) || []
);

const filteredSegments = computed(() => {
  const q = transcriptQuery.value.trim().toLowerCase();
  if (!q) return segments.value;
  return segments.value.filter(s => s.text.toLowerCase().includes(q));
});

const tabs = ['overview', 'transcript', 'analysis', 'cuts'];
function tabKey(event: KeyboardEvent) {
  const at = tabs.indexOf(tab.value);
  const next =
    event.key === 'ArrowRight'
      ? (at + 1) % 4
      : event.key === 'ArrowLeft'
        ? (at + 3) % 4
        : event.key === 'Home'
          ? 0
          : event.key === 'End'
            ? 3
            : -1;
  if (next < 0) return;
  event.preventDefault();
  tab.value = tabs[next];
  (event.currentTarget as HTMLElement)
    .querySelectorAll<HTMLButtonElement>('[role=tab]')
    [next]?.focus();
}
function seek(us: number) {
  if (player.value) {
    player.value.currentTime = us / 1e6;
    player.value.play().catch(() => {});
  }
}
</script>

<template>
  <div class="project-workspace">
    <header class="page-heading project-heading compact-project-heading">
      <el-tooltip content="Voltar para a biblioteca de projetos" placement="bottom">
        <AppButton
          class="icon-button project-back"
          aria-label="Todos os projetos"
          title="Todos os projetos"
          @click="$emit('back')"
          ><ArrowLeft :size="18"
        /></AppButton>
      </el-tooltip>
      <h1 :title="project.title || project.name">{{ project.title || project.name }}</h1>
      <div class="project-meta">
        <span :title="project.source?.channel">{{ project.source?.channel || 'Vídeo local' }}</span>
        <span>{{ project.duration_us ? time(project.duration_us) : 'Duração pendente' }}</span>
        <el-tag
          size="small"
          :type="
            project.status === 'completed'
              ? 'success'
              : project.status === 'failed'
                ? 'danger'
                : active(project.status)
                  ? 'primary'
                  : 'info'
          "
          effect="dark"
          class="status-pill"
          :data-status="project.status"
        >
          {{ projectLabel(project.status) }}
        </el-tag>
      </div>
      <el-tooltip content="Abrir pasta no Windows Explorer" placement="bottom">
        <AppButton
          class="icon-button project-folder"
          title="Abrir pasta"
          aria-label="Abrir pasta"
          @click="$emit('folder')"
          ><FolderOpen :size="18"
        /></AppButton>
      </el-tooltip>
    </header>

    <div class="project-tabs" role="tablist" aria-label="Áreas do projeto" @keydown="tabKey">
      <AppButton
        id="tab-overview"
        role="tab"
        aria-controls="project-panel"
        :tabindex="tab === 'overview' ? 0 : -1"
        :aria-selected="tab === 'overview'"
        :class="{ selected: tab === 'overview' }"
        @click="tab = 'overview'"
        ><Play :size="16" />Preparação</AppButton
      >
      <AppButton
        id="tab-transcript"
        role="tab"
        aria-controls="project-panel"
        :tabindex="tab === 'transcript' ? 0 : -1"
        :aria-selected="tab === 'transcript'"
        :class="{ selected: tab === 'transcript' }"
        @click="tab = 'transcript'"
        ><FileText :size="16" />Transcrição<span v-if="project.has_transcript">{{
          project.word_count.toLocaleString('pt-BR')
        }}</span></AppButton
      >
      <AppButton
        id="tab-analysis"
        role="tab"
        aria-controls="project-panel"
        :tabindex="tab === 'analysis' ? 0 : -1"
        :aria-selected="tab === 'analysis'"
        :class="{ selected: tab === 'analysis' }"
        @click="tab = 'analysis'"
        ><FileText :size="16" />Análise<span>{{ analysis?.proposals.length || 0 }}</span></AppButton
      >
      <AppButton
        id="tab-cuts"
        role="tab"
        aria-controls="project-panel"
        :tabindex="tab === 'cuts' ? 0 : -1"
        :aria-selected="tab === 'cuts'"
        :class="{ selected: tab === 'cuts' }"
        @click="tab = 'cuts'"
        ><Scissors :size="16" />Cortes<span>{{ revisions.length }}</span></AppButton
      >
    </div>

    <div
      class="workspace-body"
      :class="{
        'cuts-workspace': tab === 'cuts',
        'transcript-workspace': tab === 'transcript',
        'editor-workspace': tab !== 'overview',
      }"
    >
      <div id="project-panel" role="tabpanel" :aria-labelledby="'tab-' + tab">
        <!-- ABA 1: VISÃO GERAL / PREPARAÇÃO -->
        <div v-if="tab === 'overview'" class="workspace-overview">
          <PipelinePanel
            :source-url="sourceUrl"
            :selected-count="selection?.candidate_ids.length || 0"
            :selected-candidate-ids="selection?.candidate_ids"
            :project="project"
            :jobs="jobs"
            :busy="busy"
            :has-cuts="revisions.length > 0"
            :revisions="revisions"
            :analysis="analysis"
            @replace-source="$emit('replaceSource', $event)"
            @generate="
              selection?.analysis_hash &&
              $emit('render', {
                analysis_hash: selection.analysis_hash,
                candidate_ids: selection.candidate_ids,
              })
            "
            @export="$emit('export')"
            @transcribe="$emit('transcribe')"
            @analyze="$emit('analyze')"
            @render="tab = 'analysis'"
            @analysis="tab = 'analysis'"
            @review="tab = 'cuts'"
            @cancel="$emit('cancel', $event)"
            @resume="$emit('resume', $event)"
          />
        </div>

        <!-- ABA 2: TRANSCRIÇÃO (SPLIT-SCREEN DESKTOP) -->
        <section v-else-if="tab === 'transcript'" class="transcript-layout">
          <div class="transcript-header">
            <div class="transcript-header-info">
              <h2>Transcrição original</h2>
              <p>
                {{ project.word_count.toLocaleString('pt-BR') }} palavras · Português · Timestamps
                sincronizados · Consulta opcional, não bloqueia a geração de cortes
              </p>
            </div>
            <div class="transcript-search-wrap">
              <Search :size="15" />
              <input
                v-model="transcriptQuery"
                type="search"
                placeholder="Buscar termos na fala..."
              />
              <span v-if="transcriptQuery" class="search-match-count"
                >{{ filteredSegments.length }} trecho(s)</span
              >
            </div>
          </div>

          <el-splitter v-if="transcript" class="transcript-body split-transcript-body">
            <el-splitter-panel :size="380" :min="260" :max="600" class="transcript-player-column">
              <div class="panel-inner-container">
                <div class="sticky-player-wrapper">
                  <video
                    v-if="sourceUrl"
                    ref="player"
                    v-recover-media="sourceUrl"
                    :src="sourceUrl"
                    controls
                    preload="metadata"
                  ></video>
                  <div v-if="sourceUrl" class="player-playback-meta">
                    <Clock :size="13" />
                    <span>Clique em qualquer parágrafo para saltar no vídeo</span>
                  </div>
                </div>
              </div>
            </el-splitter-panel>
            <el-splitter-panel :min="320" class="transcript-segments-column">
              <div class="panel-inner-container">
                <el-scrollbar
                  height="100%"
                  class="transcript-segments"
                  tabindex="0"
                  role="region"
                  aria-label="Segmentos da transcrição"
                >
                  <div
                    v-for="segment in filteredSegments"
                    :key="segment.id"
                    role="button"
                    tabindex="-1"
                    class="transcript-segment-row"
                    :class="{
                      highlighted:
                        transcriptQuery &&
                        segment.text.toLowerCase().includes(transcriptQuery.toLowerCase()),
                    }"
                    @click="seek(segment.start_us)"
                  >
                    <time>{{ time(segment.start_us) }}</time>
                    <span>{{ segment.text }}</span>
                  </div>
                  <div v-if="filteredSegments.length === 0" class="transcript-no-matches">
                    Nenhum segmento encontrado para "{{ transcriptQuery }}".
                  </div>
                </el-scrollbar>
              </div>
            </el-splitter-panel>
          </el-splitter>
          <div v-else class="empty-state">
            <el-empty description="Ainda sem transcrição">
              <template #image>
                <FileText :size="32" />
              </template>
              <template #default>
                <p>Inicie a etapa de transcrição na visão geral.</p>
              </template>
            </el-empty>
          </div>
        </section>

        <!-- ABA 3: CURADORIA EDITORIAL DE ANÁLISE -->
        <AnalysisPanel
          v-else-if="tab === 'analysis'"
          :analysis="analysis || null"
          :selection="selection || null"
          :jobs="jobs"
          :source-url="sourceUrl"
          :busy="busy"
          @generate="$emit('render', $event)"
          @selection="$emit('selection', $event)"
          @resume="$emit('resumeAnalysis')"
        />

        <!-- ABA 4: REVISÃO DOS CORTES -->
        <section v-else>
          <ReviewPanel
            :load-media="loadMedia"
            :jobs="jobs"
            :revisions="revisions"
            :manual="project.is_manual"
            :media-url="previewUrl"
            :selected-revision="selectedRevision"
            :media-loading="mediaLoading"
            :source-url="sourceUrl"
            :busy="busy"
            :processing="processing"
            @render-final="$emit('renderFinal', $event)"
            @cancel="$emit('cancel', $event)"
            @bulk-delete="$emit('bulkDelete', $event)"
            @bulk-export="$emit('bulkExport', $event)"
            @resume="$emit('resume', $event)"
            @select="$emit('select', $event)"
            @decision="$emit('decision', $event)"
            @export="$emit('export')"
            @delete="$emit('delete', $event)"
            @deleted="$emit('deleted')"
            @retry="$emit('retry', $event)"
          />
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.transcript-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.transcript-search-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: 9px;
  padding: 6px 12px;
  color: var(--color-text-muted, var(--muted));
  min-width: 260px;
}

.transcript-search-wrap input {
  border: none;
  background: transparent;
  color: var(--color-text-primary, var(--ink));
  font-size: 0.82rem;
  width: 100%;
  outline: none;
}

.search-match-count {
  font-size: 0.72rem;
  background: var(--color-surface-hover, var(--soft));
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
}

.split-transcript-body {
  display: flex;
  flex: 1;
  height: auto;
  min-height: 0;
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: var(--radius-panel, 12px);
  overflow: hidden;
  box-sizing: border-box;
}

:deep(.el-splitter) {
  height: 100%;
  width: 100%;
}

:deep(.el-splitter__bar) {
  background: var(--color-border-subtle, var(--line));
  width: 1px;
  transition:
    background 0.15s ease,
    width 0.15s ease;
}

:deep(.el-splitter__bar:hover) {
  background: var(--color-action-primary);
  width: 3px;
}

.panel-inner-container {
  height: 100%;
  min-height: 0;
  width: 100%;
  padding: 14px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
}

.transcript-player-column .panel-inner-container {
  overflow: auto;
}

.transcript-segments-column .panel-inner-container {
  overflow: hidden;
}

.transcript-segments {
  flex: 1;
  min-height: 0;
}

.transcript-player-column,
.transcript-segments-column {
  background: transparent;
  border: none;
  border-radius: 0;
  height: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.sticky-player-wrapper video {
  width: 100%;
  aspect-ratio: 16/9;
  border-radius: 8px;
  background: #000;
  display: block;
  border: 1px solid var(--color-border-subtle, var(--line));
}

.player-playback-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.73rem;
  color: var(--color-text-muted, var(--muted));
  margin-top: 10px;
  padding: 0 4px;
}

.transcript-segment-row {
  transition: background 0.12s ease;
}

.transcript-segment-row.highlighted {
  background: var(--color-surface-selected);
  border-color: var(--color-border-strong);
}

.transcript-no-matches {
  padding: 24px;
  text-align: center;
  color: var(--color-text-muted, var(--muted));
  font-size: 0.85rem;
}
</style>
