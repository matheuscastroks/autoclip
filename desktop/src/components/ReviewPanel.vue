<script setup lang="ts">
import { computed, ref, watch, toRef } from 'vue';
import AppButton from './AppButton.vue';
import ClipPreviewDrawer from './ClipPreviewDrawer.vue';
import { vRecoverMedia } from '../directives/recoverMedia';
import type { Revision, Decision, Job, GenerationItem } from '../types';
import { time, labels, active, latestJob } from '../format';
import { useBulkSelection } from '../composables/useBulkSelection';
import { isFinalAvailable, isExportable } from '../domain/revisionPresentation';

const props = defineProps<{
  revisions: Revision[];
  manual: boolean;
  mediaUrl: string;
  sourceUrl: string;
  loadMedia?: (asset: string) => Promise<string>;
  busy?: boolean;
  selectedRevision?: string;
  mediaLoading?: boolean;
  processing?: boolean;
  jobs?: Job[];
}>();
const emit = defineEmits<{
  select: [id: string];
  decision: [value: Decision];
  export: [];
  delete: [id: string];
  deleted: [];
  resume: [id: string];
  cancel: [id: string];
  renderFinal: [id: string];
  retry: [value: { job_id: string; candidate_id: string }];
  bulkDelete: [ids: string[]];
  bulkExport: [ids: string[]];
}>();
const filter = ref('all');
const order = ref('recent');
const selected = ref('');
const drawerOpen = ref(false);
const deleteBlockedReason = computed(() =>
  props.busy
    ? 'Aguarde a operação atual.'
    : (props.jobs || []).some(
          j => active(j.status) && !['transcribe', 'analyze'].includes(j.operation)
        ) ||
        (!props.jobs && props.processing)
      ? 'Aguarde ou cancele a geração, exportação ou importação para excluir este corte.'
      : ''
);
const current = computed(() =>
  props.revisions.find(r => r.revision_id === (props.selectedRevision || selected.value))
);
watch(
  () => props.selectedRevision,
  id => {
    if (id) selected.value = id;
  }
);
watch(
  () => props.revisions,
  rows => {
    if (drawerOpen.value && !rows.some(r => r.revision_id === selected.value))
      drawerOpen.value = false;
  }
);
const renderJob = computed(() =>
  latestJob(
    (props.jobs || []).filter(j => ['render', 'preview', 'render_final'].includes(j.operation))
  )
);
const phases: Record<string, string> = {
  waiting: 'Na fila',
  edit_plan: 'Preparando cortes',
  pauses: 'Verificando pausas',
  captions: 'Sincronizando legendas',
  reframe: 'Acompanhando rosto',
  render: 'Gerando prévia',
  render_final: 'Renderizando versão final',
  verify: 'Validando versão final',
  ready: 'Disponível',
  failed: 'Falha neste corte',
};
const generationItems = computed(() => {
  const seen = new Set<string>();
  const items: (GenerationItem & {
    retry_job_id: string;
    operation: string;
    job_status: Job['status'];
  })[] = [];
  for (const job of [...(props.jobs || [])]
    .filter(j => ['render', 'preview', 'render_final'].includes(j.operation))
    .sort((a, b) => b.created_at.localeCompare(a.created_at) || b.id.localeCompare(a.id))) {
    for (const item of job.progress?.items || []) {
      const key =
        job.operation + (job.operation === 'render_final' ? item.revision_id : item.candidate_id);
      if (seen.has(key)) continue;
      seen.add(key);
      if (!['ready', 'cancelled'].includes(item.state))
        items.push({
          ...item,
          retry_job_id: job.id,
          operation: job.operation,
          job_status: job.status,
        });
    }
  }
  return items;
});
function outputJob(r: Revision) {
  return generationItems.value.find(i => i.revision_id === r.revision_id);
}
const visibleRevisions = computed(() => {
  const rows = props.revisions.filter(
    r =>
      filter.value === 'all' ||
      (filter.value === 'generation' && !!outputJob(r)) ||
      (filter.value === 'approved' && isExportable(r)) ||
      (filter.value === 'review' &&
        isFinalAvailable(r) &&
        ['needs_review', 'stale_review'].includes(r.review_status)) ||
      (filter.value === 'exported' && r.exported)
  );
  return order.value === 'title'
    ? rows.sort((a, b) => a.title.localeCompare(b.title))
    : order.value === 'duration'
      ? rows.sort((a, b) => (b.duration_us || 0) - (a.duration_us || 0))
      : rows.slice().reverse();
});
const visibleGeneration = computed(() =>
  ['all', 'generation'].includes(filter.value)
    ? generationItems.value.filter(i => !props.revisions.some(r => r.revision_id === i.revision_id))
    : []
);
const { bulk, allVisible, exportableBulk, toggleAll } = useBulkSelection(
  toRef(props, 'revisions'),
  visibleRevisions
);
function choose(id: string) {
  selected.value = id;
  emit('select', id);
  drawerOpen.value = true;
}
function finalLabel(r: Revision) {
  const job = outputJob(r);
  if (job?.operation === 'render_final' && ['interrupted', 'cancelled'].includes(job.job_status))
    return job.job_status === 'interrupted' ? 'Final interrompida' : 'Final cancelada';
  if (job)
    return job.operation === 'render_final'
      ? job.state === 'failed'
        ? 'Falha no final'
        : phases[job.phase] || 'Render final na fila'
      : phases[job.phase] || 'Em geração';
  if (r.final_state === 'not_generated') return 'Final não gerada';
  if (r.final_state === 'invalid') return 'Final inválida';
  return isFinalAvailable(r) ? 'Final disponível' : 'Final indisponível';
}
</script>

<template>
  <div v-if="manual" class="manual-review">
    <h2>Prévia manual de renderização</h2>
    <p>Teste técnico, sem aprovação editorial.</p>
    <video
      v-if="mediaUrl"
      v-recover-media="mediaUrl"
      class="manual-player"
      :src="mediaUrl"
      controls
      preload="metadata"
      playsinline
    />
  </div>
  <div v-else class="cuts-review-layout">
    <header class="cuts-table-heading">
      <h2>
        Cortes <span>{{ revisions.length }}</span>
      </h2>
      <AppButton
        :disabled="busy || processing || !revisions.some(isExportable)"
        @click="$emit('export')"
        >Exportar aprovados</AppButton
      >
    </header>
    <div class="cuts-list-toolbar">
      <div class="cuts-filters" aria-label="Filtrar cortes">
        <button
          v-for="[id, label] in [
            ['all', 'Todos'],
            ['generation', 'Em geração'],
            ['review', 'Para revisar'],
            ['approved', 'Aprovados'],
            ['exported', 'Exportados'],
          ]"
          :key="id"
          type="button"
          class="cuts-filter-chip"
          :class="{ selected: filter === id }"
          :aria-pressed="filter === id"
          @click="filter = id"
        >
          {{ label }}
        </button>
      </div>
      <select v-model="order" aria-label="Ordenar cortes">
        <option value="recent">Mais recentes</option>
        <option value="title">Título</option>
        <option value="duration">Duração</option>
      </select>
      <AppButton class="cuts-trash" @click="$emit('deleted')">Lixeira</AppButton>
    </div>
    <div
      v-if="
        renderJob &&
        ['failed', 'cancelled', 'interrupted'].includes(renderJob.status) &&
        generationItems.length
      "
      class="render-resume-banner"
    >
      <span>Há cortes pendentes. Os arquivos concluídos foram preservados.</span
      ><AppButton :disabled="busy" @click="$emit('resume', renderJob.id)"
        >Continuar pendentes</AppButton
      >
    </div>
    <div v-if="bulk.length" class="bulk-actions">
      <span>{{ bulk.length }} selecionado(s)</span>
      <AppButton :disabled="!!deleteBlockedReason" @click="$emit('bulkDelete', [...bulk])"
        >Excluir selecionados</AppButton
      >
      <AppButton
        :disabled="busy || processing || !exportableBulk"
        @click="$emit('bulkExport', [...bulk])"
        >Exportar selecionados</AppButton
      >
      <AppButton @click="bulk = []">Limpar seleção</AppButton>
    </div>
    <div v-if="visibleRevisions.length || visibleGeneration.length" class="cuts-table-scroll">
      <table class="cuts-table" aria-label="Cortes disponíveis">
        <thead>
          <tr>
            <th scope="col" class="bulk-check">
              <input
                v-if="visibleRevisions.length"
                type="checkbox"
                aria-label="Selecionar todos os cortes visíveis"
                :checked="allVisible"
                :indeterminate="
                  !allVisible && visibleRevisions.some(r => bulk.includes(r.revision_id))
                "
                @change="toggleAll"
              />
            </th>
            <th scope="col">Corte</th>
            <th scope="col">Duração</th>
            <th scope="col">Prévia</th>
            <th scope="col">Versão final</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="r in visibleRevisions"
            :key="r.revision_id"
            class="clip-item"
            :class="{ selected: current?.revision_id === r.revision_id }"
            :aria-selected="current?.revision_id === r.revision_id"
            tabindex="0"
            @click="choose(r.revision_id)"
            @keydown.enter.prevent="choose(r.revision_id)"
            @keydown.space.prevent="choose(r.revision_id)"
          >
            <td class="bulk-check" @click.stop @keydown.stop>
              <input
                v-model="bulk"
                type="checkbox"
                :value="r.revision_id"
                :aria-label="'Selecionar corte: ' + r.title"
              />
            </td>
            <td>
              <button type="button" class="clip-open" @click.stop="choose(r.revision_id)">
                {{ r.title }}
              </button>
            </td>
            <td>{{ time(r.duration_us) }}</td>
            <td>
              {{
                r.preview?.state === 'available'
                  ? 'Prévia disponível'
                  : r.preview?.state === 'invalid'
                    ? 'Prévia inválida'
                    : r.final_state === 'not_generated'
                      ? 'Aguardando prévia'
                      : 'Final legada'
              }}
            </td>
            <td>
              <span>{{ finalLabel(r) }}</span
              ><small data-editorial-status>{{
                isFinalAvailable(r) ? labels[r.review_status] : 'Revisão após validação final'
              }}</small
              ><progress
                v-if="outputJob(r)?.total_us"
                :value="outputJob(r)?.processed_us"
                :max="outputJob(r)?.total_us || 1"
              />
            </td>
          </tr>
          <tr
            v-for="item in visibleGeneration"
            :key="item.retry_job_id + item.candidate_id"
            class="clip-item-generating"
            :data-state="item.state"
          >
            <td></td>
            <td>
              <strong>{{ item.title }}</strong>
              <p v-if="item.error_message">{{ item.error_message }}</p>
            </td>
            <td>{{ time(item.total_us) }}</td>
            <td colspan="2">
              {{ phases[item.phase] || 'Na fila' }}
              <progress v-if="item.total_us" :value="item.processed_us" :max="item.total_us" />
              <AppButton
                v-if="item.state === 'failed'"
                class="retry-btn"
                :aria-label="'Tentar novamente: ' + item.title"
                @click="
                  $emit('retry', { job_id: item.retry_job_id, candidate_id: item.candidate_id })
                "
                >Tentar novamente</AppButton
              >
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="empty-state cuts-empty">
      <h3>
        {{
          !revisions.length && !generationItems.length
            ? 'Nenhum corte disponível'
            : 'Nenhum corte neste estado'
        }}
      </h3>
      <p>
        Na aba Análise, selecione propostas e gere prévias rápidas. Abra um corte para avaliar e
        solicitar sua versão final.
      </p>
    </div>
    <ClipPreviewDrawer
      v-model="drawerOpen"
      :revision="current"
      :load-media="loadMedia"
      :media-url="mediaUrl"
      :source-url="sourceUrl"
      :jobs="jobs"
      :busy="busy"
      :delete-blocked-reason="deleteBlockedReason"
      @render-final="$emit('renderFinal', $event)"
      @cancel="$emit('cancel', $event)"
      @resume="$emit('resume', $event)"
      @decision="$emit('decision', $event)"
      @delete="$emit('delete', $event)"
      @export="$emit('export')"
    />
  </div>
</template>

<style scoped>
.cuts-review-layout {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  min-height: 0;
  min-width: 0;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--radius-panel);
  padding: 20px;
}
.cuts-table-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}
.cuts-table-heading h2 {
  margin: 0;
  font-size: var(--font-size-region);
}
.cuts-table-heading h2 span {
  color: var(--muted);
  font-size: 12px;
  margin-left: 8px;
}
.cuts-list-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}
.cuts-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.cuts-filter-chip {
  border: 1px solid transparent;
  border-radius: var(--radius-control);
  color: var(--muted);
  background: transparent;
  padding: 7px 10px;
  cursor: pointer;
  font-size: 12px;
}
.cuts-filter-chip.selected {
  background: var(--soft);
  color: var(--ink);
  border-color: var(--line);
}
.cuts-list-toolbar select {
  color: var(--color-text-secondary);
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--radius-control);
  padding: 6px;
  font-size: 12px;
  margin-left: auto;
}
.cuts-table-scroll {
  min-height: 0;
  flex: 1;
  overflow: auto;
  max-height: none;
  overscroll-behavior: contain;
}
.cuts-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-control);
}
.cuts-table [data-editorial-status] {
  display: block;
  margin-top: 4px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-meta);
}
.cuts-table th {
  text-align: left;
  color: var(--muted);
  font-weight: 500;
  position: sticky;
  top: 0;
  background: var(--panel);
  z-index: 1;
}
.cuts-table th,
.cuts-table td {
  padding: 14px 12px;
  border-bottom: 1px solid var(--line);
  vertical-align: middle;
}
.cuts-table th:first-child,
.cuts-table td:first-child {
  width: 32px;
  padding-left: 0;
}
.cuts-table tr.clip-item {
  display: table-row;
  width: auto;
  text-align: left;
  cursor: pointer;
}
.cuts-table tr.clip-item:hover,
.cuts-table tr.selected {
  background: var(--soft);
}
.clip-open {
  padding: 0;
  color: var(--ink);
  background: none;
  border: 0;
  font: inherit;
  font-weight: 500;
  text-align: left;
  cursor: pointer;
  overflow-wrap: anywhere;
}
.cuts-table td:nth-child(2) {
  width: 40%;
  min-width: 160px;
}
.cuts-table progress {
  display: block;
  width: 100%;
  height: 5px;
  margin-top: 6px;
}
.bulk-actions,
.render-resume-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  padding-block: 8px;
}
.clip-item-generating p {
  color: var(--color-warning-text);
}
.manual-player {
  max-height: 60vh;
  max-width: 100%;
}
</style>
