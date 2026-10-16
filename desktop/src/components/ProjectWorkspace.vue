<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import AppButton from './AppButton.vue';
import TranscriptPanel from './TranscriptPanel.vue';
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
import WorkspaceHeader from './layout/WorkspaceHeader.vue';
import ProjectTabs, { type ProjectTab } from './layout/ProjectTabs.vue';
import ReviewPanel from './ReviewPanel.vue';
import PipelinePanel from './PipelinePanel.vue';
import AnalysisPanel from './AnalysisPanel.vue';

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
  previewError?: string | null;
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
  dismissPreviewError: [];
}>();

const tab = defineModel<ProjectTab>('activeTab', { default: 'overview' });
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
const currentSelection = computed(() =>
  props.analysis?.state === 'completed' &&
  props.analysis.analysis_hash &&
  props.selection?.analysis_hash === props.analysis.analysis_hash
    ? props.selection
    : null
);
</script>

<template>
  <div class="project-workspace">
    <WorkspaceHeader
      :title="project.title || project.name"
      project
      @back="$emit('back')"
      @folder="$emit('folder')"
    >
      <template #metadata>
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
          >{{ projectLabel(project.status) }}</el-tag
        >
      </template>
    </WorkspaceHeader>
    <ProjectTabs
      v-model="tab"
      :counts="{
        transcript: project.has_transcript ? project.word_count : undefined,
        analysis: analysis?.proposals.length,
        cuts: revisions.length,
      }"
    />

    <section v-if="previewError" class="preview-failure" data-preview-failure role="alert">
      <div class="preview-failure-copy">
        <strong>Não foi possível gerar as prévias</strong>
        <p>Revise a seleção na Análise ou tente novamente.</p>
        <details>
          <summary>Detalhes do erro</summary>
          <p class="preview-failure-detail">{{ previewError }}</p>
        </details>
      </div>
      <div class="preview-failure-actions">
        <AppButton
          class="button secondary"
          data-action="retry-previews"
          :disabled="busy || !currentSelection?.candidate_ids.length"
          @click="
            $emit('dismissPreviewError');
            currentSelection &&
              $emit('render', {
                analysis_hash: currentSelection.analysis_hash!,
                candidate_ids: [...currentSelection.candidate_ids],
              });
          "
          >Tentar novamente</AppButton
        >
        <button type="button" class="text-button" @click="$emit('dismissPreviewError')">
          Dispensar
        </button>
      </div>
    </section>

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
            :selected-count="currentSelection?.candidate_ids.length || 0"
            :selected-candidate-ids="currentSelection?.candidate_ids || []"
            :project="project"
            :jobs="jobs"
            :busy="busy"
            :has-cuts="revisions.length > 0"
            :revisions="revisions"
            :analysis="analysis"
            @replace-source="$emit('replaceSource', $event)"
            @generate="
              currentSelection?.candidate_ids.length &&
              $emit('render', {
                analysis_hash: currentSelection.analysis_hash!,
                candidate_ids: currentSelection.candidate_ids,
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

        <TranscriptPanel
          v-else-if="tab === 'transcript'"
          v-model:query="transcriptQuery"
          :transcript="transcript"
          :source-url="sourceUrl"
          :word-count="project.word_count"
        />

        <!-- ABA 3: CURADORIA EDITORIAL DE ANÁLISE -->
        <AnalysisPanel
          v-else-if="tab === 'analysis'"
          :analysis="analysis || null"
          :selection="selection || null"
          :jobs="jobs"
          :source-url="sourceUrl"
          :busy="busy"
          :load-source="loadMedia ? () => loadMedia!('source') : undefined"
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
.preview-failure {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 12px 0;
  border-block: 1px solid var(--color-border-subtle);
}
.preview-failure-copy {
  min-width: 0;
}
.preview-failure-copy p,
.preview-failure-detail {
  margin-top: 4px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-meta);
}
.preview-failure-copy details {
  margin-top: 6px;
  font-size: var(--font-size-meta);
}
.preview-failure-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}
@media (max-width: 720px) {
  .preview-failure {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
