<script setup lang="ts">
import AppButton from './AppButton.vue';
import { computed, ref, watch } from 'vue';
import {
  Scissors,
  Info,
  Download,
  Trash2,
  Check,
  Clock,
  Film,
  Copy,
  X,
  LoaderCircle,
  AlertCircle,
  RotateCcw,
} from '@lucide/vue';
import type { Revision, Checks, Decision, Job, GenerationItem } from '../types';
import { notify } from '../notifications';
import { time, labels, latestJob, active } from '../format';

const props = defineProps<{
  revisions: Revision[];
  manual: boolean;
  mediaUrl: string;
  sourceUrl: string;
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
  retry: [value: { job_id: string; candidate_id: string }];
  bulkDelete: [ids: string[]];
  bulkExport: [ids: string[]];
}>();

const filter = ref('all');
const deleteBlockedReason = computed(() =>
  props.busy
    ? 'Aguarde a operação atual.'
    : (props.jobs || []).some(
          j => active(j.status) && !['transcribe', 'analyze'].includes(j.operation)
        )
      ? 'Aguarde ou cancele a geração, exportação ou importação para excluir este corte.'
      : !props.jobs && props.processing
        ? 'Aguarde o processamento para excluir este corte.'
        : ''
);

const phases: Record<string, string> = {
  waiting: 'Na fila',
  edit_plan: 'Preparando edição',
  pauses: 'Verificando pausas',
  reframe: 'Acompanhando rosto',
  captions: 'Sincronizando legendas',
  render: 'Codificando vídeo',
  verify: 'Verificando áudio e vídeo',
  ready: 'Pronta para revisar',
  failed: 'Falha neste corte',
};
const statePriority: Record<string, number> = { running: 0, failed: 1, waiting: 2, ready: 3 };

const renderJob = computed(() =>
  latestJob((props.jobs || []).filter(j => j.operation === 'render'))
);

const generationItems = computed(() => {
  if (!props.jobs) return [];
  const seen = new Set<string>();
  const items: (GenerationItem & { retry_job_id: string })[] = [];
  for (const row of [...props.jobs]
    .filter(j => j.operation === 'render')
    .sort((a, b) => b.created_at.localeCompare(a.created_at) || b.id.localeCompare(a.id))) {
    for (const item of row.progress?.items || []) {
      if (seen.has(item.candidate_id)) continue;
      seen.add(item.candidate_id);
      if (!['ready', 'cancelled'].includes(item.state)) {
        items.push({ ...item, retry_job_id: row.id });
      }
    }
  }
  return items.sort((a, b) => (statePriority[a.state] ?? 2) - (statePriority[b.state] ?? 2));
});

const hasCutsOrGeneration = computed(
  () => props.revisions.length > 0 || generationItems.value.length > 0
);

const visibleRevisions = computed(() => {
  if (filter.value === 'generation') return [];
  return props.revisions.filter(
    r =>
      filter.value === 'all' ||
      (filter.value === 'approved' && r.technical_pass) ||
      (filter.value === 'review' && r.review_status === 'needs_review') ||
      (filter.value === 'exported' && r.exported)
  );
});

const visibleGeneration = computed(() => {
  if (['approved', 'exported', 'review'].includes(filter.value)) return [];
  return generationItems.value;
});

const visible = visibleRevisions;
const totalCutsCount = computed(() => {
  if (filter.value === 'generation') return visibleGeneration.value.length;
  return visibleRevisions.value.length + visibleGeneration.value.length;
});

const bulk = ref<string[]>([]);
const allVisible = computed(
  () =>
    visibleRevisions.value.length > 0 &&
    visibleRevisions.value.every(r => bulk.value.includes(r.revision_id))
);
const exportableBulk = computed(
  () =>
    bulk.value.length > 0 &&
    bulk.value.every(id => props.revisions.some(r => r.revision_id === id && r.technical_pass))
);

watch(
  () => props.revisions,
  rows => {
    bulk.value = bulk.value.filter(id => rows.some(r => r.revision_id === id));
  }
);
function toggleAll() {
  const ids = visibleRevisions.value.map(r => r.revision_id);
  bulk.value = allVisible.value
    ? bulk.value.filter(id => !ids.includes(id))
    : [...new Set([...bulk.value, ...ids])];
}

const selected = ref('');
watch(
  () => props.selectedRevision,
  id => {
    if (
      id &&
      props.revisions.some(r => r.revision_id === id) &&
      !visibleRevisions.value.some(r => r.revision_id === id)
    )
      filter.value = 'all';
  },
  { flush: 'sync' }
);
const current = computed(
  () =>
    visibleRevisions.value.find(
      r => r.revision_id === (props.selectedRevision || selected.value)
    ) || visibleRevisions.value[0]
);
watch(
  visibleRevisions,
  rows => {
    if (props.selectedRevision && rows.some(r => r.revision_id === props.selectedRevision)) {
      selected.value = props.selectedRevision;
      return;
    }
    if (!rows.some(r => r.revision_id === selected.value) && rows.length) {
      selected.value = rows[0].revision_id;
      emit('select', selected.value);
    }
  },
  { immediate: true }
);
watch(
  current,
  value => {
    if (value && !value.technical_pass)
      notify.error('A verificação técnica falhou. Gere a prévia novamente.', {
        key: 'revision:' + value.revision_id + ':' + value.content_hash,
      });
  },
  { immediate: true }
);

function choose(id: string) {
  selected.value = id;
  emit('select', id);
}

function makeDecision(decision: 'approved' | 'rejected') {
  if (!current.value) return;
  emit('decision', {
    revision_id: current.value.revision_id,
    decision,
    checks: {
      completeness: true,
      context: true,
      qualifications: true,
      words_and_boundaries: true,
      audiovisual: true,
    },
    notes: '',
    content_hash: current.value.content_hash || '',
  });
}

function copyDescription() {
  if (current.value?.description) {
    navigator.clipboard
      .writeText(current.value.description)
      .then(() => {
        notify.success('Descrição copiada para a área de transferência.');
      })
      .catch(() => {});
  }
}
</script>

<template>
  <div v-if="manual" class="manual-review">
    <div class="subtle">
      <Info :size="19" />
      <div>
        <strong>Prévia manual de renderização</strong>
        <p>
          Este trecho é um teste técnico. Não foi selecionado pelo Gemini e não está aprovado
          editorialmente.
        </p>
      </div>
    </div>
    <video
      v-if="mediaUrl"
      class="manual-player"
      :src="mediaUrl"
      controls
      preload="metadata"
      playsinline
    ></video>
  </div>

  <div v-if="!manual && !hasCutsOrGeneration" class="empty-state cuts-empty">
    <el-empty description="Nenhum corte disponível">
      <template #image>
        <span class="empty-icon"><Scissors :size="32" /></span>
      </template>
      <template #default>
        <p>
          A transcrição pode ser consultada. Na aba Análise, escolha propostas e gere prévias. Cada
          prévia aparece aqui após a verificação técnica.
        </p>
        <span class="subtle">Os cortes ficam disponíveis após a validação técnica.</span>
      </template>
    </el-empty>
  </div>

  <el-splitter v-if="!manual && hasCutsOrGeneration" class="cuts-review-layout">
    <el-splitter-panel :size="800" :min="380" class="cuts-review-left-panel">
      <div class="panel-inner-container custom-scrollbar">
        <div class="cuts-review-left">
          <!-- BARRA DE FILTROS DOS CORTES -->
          <div class="cuts-filters" aria-label="Filtrar cortes">
            <AppButton
              v-for="[id, label] in [
                ['all', 'Todos'],
                ['generation', 'Em geração'],
                ['approved', 'Prontos'],
                ['exported', 'Exportados'],
              ]"
              :key="id"
              :class="{ selected: filter === id }"
              :aria-pressed="filter === id"
              class="cuts-filter-chip"
              @click="filter = id"
            >
              {{ label }}
            </AppButton>
            <el-tooltip content="Ver cortes movidos para a lixeira" placement="top">
              <AppButton
                type="button"
                class="button secondary cuts-trash"
                @click="$emit('deleted')"
              >
                <Trash2 :size="14" />Lixeira de cortes
              </AppButton>
            </el-tooltip>
          </div>

          <!-- BANNER DE RETOMADA SE O JOB FOI INTERROMPIDO -->
          <div
            v-if="
              renderJob &&
              ['failed', 'cancelled', 'interrupted'].includes(renderJob.status) &&
              visibleGeneration.length
            "
            class="render-resume-banner"
          >
            <span>A renderização anterior foi interrompida ou apresentou falhas em prévias.</span>
            <AppButton class="button small secondary" @click="$emit('resume', renderJob.id)"
              >Continuar prévias pendentes</AppButton
            >
          </div>

          <p v-if="filter === 'generation' && !visibleGeneration.length" class="subtle">
            Nenhuma prévia em geração no momento.
          </p>
          <p
            v-else-if="
              filter !== 'generation' && !visibleRevisions.length && !visibleGeneration.length
            "
            class="subtle"
          >
            Nenhum corte neste estado.
          </p>

          <div v-if="visibleRevisions.length || visibleGeneration.length" class="review-grid">
            <!-- TABELA / LISTA DE CORTES GERADOS E EM GERAÇÃO -->
            <section class="clip-list cuts-table-section">
              <header class="cuts-table-heading">
                <div class="table-heading-title">
                  <Film :size="16" />
                  <h3>
                    Cortes <span>{{ totalCutsCount }}</span>
                  </h3>
                </div>
                <AppButton
                  class="button small secondary"
                  :disabled="busy || processing || !revisions.some(r => r.technical_pass)"
                  @click="$emit('export')"
                >
                  <Download :size="14" />Exportar prontos
                </AppButton>
              </header>

              <!-- AÇÕES EM LOTE (BULK ACTIONS) -->
              <div v-if="bulk.length" class="bulk-actions">
                <span class="bulk-count">{{ bulk.length }} selecionado(s)</span>
                <AppButton
                  class="button small danger"
                  :disabled="!!deleteBlockedReason"
                  @click="$emit('bulkDelete', [...bulk])"
                >
                  Excluir selecionados
                </AppButton>
                <AppButton
                  class="button small secondary"
                  :disabled="busy || processing || !exportableBulk"
                  @click="$emit('bulkExport', [...bulk])"
                >
                  Exportar selecionados
                </AppButton>
                <AppButton class="button small secondary" @click="bulk = []"
                  >Limpar seleção</AppButton
                >
                <span v-if="!exportableBulk" class="subtle"
                  >A exportação exige todos os selecionados tecnicamente válidos.</span
                >
              </div>

              <el-scrollbar max-height="320px" class="cuts-table-scroll">
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
                      <th scope="col">Original</th>
                      <th scope="col">Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    <!-- CORTES FINALIZADOS (REVISÕES) -->
                    <tr
                      v-for="(r, index) in visibleRevisions"
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
                          type="checkbox"
                          v-model="bulk"
                          :value="r.revision_id"
                          :aria-label="'Selecionar corte: ' + r.title"
                        />
                      </td>
                      <td>
                        <span class="clip-number">{{ index + 1 }}</span>
                        <strong>{{ r.title }}</strong>
                      </td>
                      <td>{{ time(r.duration_us) }}</td>
                      <td>{{ time(r.start_us) }} – {{ time(r.end_us) }}</td>
                      <td>
                        <el-tag
                          size="small"
                          :type="
                            r.review_status === 'approved'
                              ? 'success'
                              : r.review_status === 'rejected'
                                ? 'danger'
                                : 'warning'
                          "
                          effect="dark"
                          class="status-pill"
                          :data-status="r.review_status"
                        >
                          {{ labels[r.review_status] || r.review_status }}
                        </el-tag>
                      </td>
                    </tr>

                    <!-- CORTES EM GERAÇÃO / PROCESSAMENTO OU COM FALHA -->
                    <tr
                      v-for="item in visibleGeneration"
                      :key="item.candidate_id"
                      class="clip-item clip-item-generating"
                      :data-state="item.state"
                    >
                      <td class="bulk-check">
                        <span class="item-state-dot" :data-state="item.state"></span>
                      </td>
                      <td>
                        <div class="generating-title-cell">
                          <strong>{{ item.title || 'Trecho selecionado' }}</strong>
                          <div v-if="item.error_code" class="generating-error-snippet">
                            <small
                              >{{
                                item.error_stage
                                  ? phases[item.error_stage] || item.error_stage
                                  : 'Geração'
                              }}
                              · {{ item.error_code }}:
                              {{ item.error_message || 'Falha na renderização' }}</small
                            >
                          </div>
                        </div>
                      </td>
                      <td>
                        <span v-if="item.processed_us && item.total_us" class="subtle-time">{{
                          time(item.processed_us)
                        }}</span>
                        <span v-else class="subtle">—</span>
                      </td>
                      <td>
                        <div
                          v-if="['render', 'reframe'].includes(item.phase) && item.total_us"
                          class="row-progress-cell"
                        >
                          <el-progress
                            :percentage="
                              Math.min(100, Math.floor((item.processed_us / item.total_us) * 100))
                            "
                            :stroke-width="5"
                            :show-text="false"
                            color="#d97724"
                          />
                          <small
                            >{{
                              Math.min(100, Math.floor((item.processed_us / item.total_us) * 100))
                            }}% {{ item.phase === 'reframe' ? 'rosto' : 'vídeo' }}</small
                          >
                        </div>
                        <span v-else class="subtle-phase">{{
                          phases[item.phase] || item.phase
                        }}</span>
                      </td>
                      <td>
                        <div class="generating-status-action">
                          <el-tag
                            size="small"
                            :type="
                              item.state === 'running'
                                ? 'primary'
                                : item.state === 'failed'
                                  ? 'danger'
                                  : 'info'
                            "
                            effect="dark"
                            class="status-pill"
                            :data-status="item.state"
                          >
                            <LoaderCircle v-if="item.state === 'running'" class="spin" :size="12" />
                            <AlertCircle v-else-if="item.state === 'failed'" :size="12" />
                            <Clock v-else :size="12" />
                            {{
                              item.state === 'running'
                                ? 'Renderizando'
                                : item.state === 'failed'
                                  ? 'Falha'
                                  : 'Na fila'
                            }}
                          </el-tag>
                          <AppButton
                            v-if="item.state === 'failed'"
                            type="button"
                            class="button small secondary retry-btn"
                            :aria-label="'Tentar novamente: ' + item.title"
                            @click.stop="
                              $emit('retry', {
                                job_id: item.retry_job_id,
                                candidate_id: item.candidate_id,
                              })
                            "
                          >
                            <RotateCcw :size="12" /> Tentar novamente
                          </AppButton>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </el-scrollbar>
            </section>

            <!-- PAINEL DE INFORMAÇÕES E ENTREGA DO CORTE SELECIONADO -->
            <section v-if="current" class="clip-information">
              <div class="clip-info-topbar">
                <AppButton
                  type="button"
                  class="button small danger delete-cut-btn"
                  :disabled="!!deleteBlockedReason"
                  :title="deleteBlockedReason || 'Mover corte para a lixeira'"
                  :aria-describedby="deleteBlockedReason ? 'delete-blocked-reason' : undefined"
                  data-action="delete-clip"
                  @click="current && $emit('delete', current.revision_id)"
                >
                  <Trash2 :size="13" />Excluir corte
                </AppButton>
                <p
                  v-if="deleteBlockedReason"
                  id="delete-blocked-reason"
                  class="subtle delete-blocked-text"
                >
                  {{ deleteBlockedReason }}
                </p>
              </div>

              <h2 class="preview-label">{{ current?.title }}</h2>

              <div class="clip-meta-strip" v-if="current">
                <el-tag size="small" effect="plain" class="meta-tag"
                  ><Clock :size="12" /> {{ time(current.duration_us) }}</el-tag
                >
                <el-tag size="small" effect="plain" class="meta-tag"
                  >Trecho: {{ time(current.start_us) }} às {{ time(current.end_us) }}</el-tag
                >
                <el-tag
                  size="small"
                  :type="
                    current.review_status === 'approved'
                      ? 'success'
                      : current.review_status === 'rejected'
                        ? 'danger'
                        : 'warning'
                  "
                  effect="dark"
                  class="status-pill"
                  :data-status="current.review_status"
                >
                  {{ labels[current.review_status] || current.review_status }}
                </el-tag>
              </div>

              <!-- Controle de Decisão Editorial (Aprovar / Descartar) -->
              <div class="cut-decision-controls" v-if="current && !manual">
                <span class="decision-heading">Decisão Editorial:</span>
                <div class="decision-btn-group">
                  <AppButton
                    type="button"
                    class="button small decision-btn approve-btn"
                    :class="{ active: current.review_status === 'approved' }"
                    data-action="editorial-approve"
                    :title="
                      current.review_status === 'approved'
                        ? 'Corte aprovado para publicação'
                        : 'Aprovar corte para publicação'
                    "
                    @click="makeDecision('approved')"
                  >
                    <Check :size="13" />
                    <span>{{
                      current.review_status === 'approved'
                        ? 'Aprovado para publicação'
                        : 'Aprovar corte'
                    }}</span>
                  </AppButton>
                  <AppButton
                    type="button"
                    class="button small decision-btn reject-btn"
                    :class="{ active: current.review_status === 'rejected' }"
                    data-action="editorial-reject"
                    :title="
                      current.review_status === 'rejected'
                        ? 'Corte descartado'
                        : 'Descartar este corte'
                    "
                    @click="makeDecision('rejected')"
                  >
                    <X :size="13" />
                    <span>{{
                      current.review_status === 'rejected' ? 'Descartado' : 'Descartar corte'
                    }}</span>
                  </AppButton>
                </div>
              </div>

              <el-divider border-style="dashed" style="margin: 16px 0" />

              <!-- Cópia Editorial para Redes Sociais -->
              <div class="clip-copy">
                <div class="copy-header-row">
                  <h3>Descrição para publicação</h3>
                  <el-tooltip
                    v-if="current?.description"
                    content="Copiar texto para área de transferência"
                    placement="top"
                  >
                    <AppButton
                      class="button small secondary copy-btn"
                      title="Copiar descrição"
                      @click="copyDescription"
                    >
                      <Copy :size="13" />Copiar
                    </AppButton>
                  </el-tooltip>
                </div>
                <div class="description-box">
                  <p style="white-space: pre-line">
                    {{ current?.description || 'Sem descrição gerada para este corte.' }}
                  </p>
                </div>

                <!-- Botão de Download Principal do Arquivo MP4 9:16 -->
                <div class="download-action-box">
                  <a
                    v-if="current?.technical_pass && mediaUrl && !mediaLoading"
                    class="button primary download-main-btn"
                    :href="mediaUrl + (mediaUrl.includes('?') ? '&' : '?') + 'download=1'"
                    download
                  >
                    <Download :size="16" />Baixar vídeo (MP4 9:16)
                  </a>
                  <p v-else class="subtle">Download disponível após a validação técnica.</p>
                </div>
              </div>
            </section>
          </div>
        </div>
      </div>
    </el-splitter-panel>

    <!-- PLAYER VERTICAL 9:16 CALIBRADO (COLUNA DA DIREITA) -->
    <el-splitter-panel :size="320" :min="260" :max="480" class="cuts-player-rail-panel">
      <div class="panel-inner-container custom-scrollbar player-rail-container">
        <aside
          v-if="visibleRevisions.length && filter !== 'generation'"
          class="cuts-player-rail"
          aria-label="Prévia do corte selecionado"
        >
          <div class="clip-preview">
            <video v-if="mediaUrl" :src="mediaUrl" controls preload="metadata" playsinline></video>
            <div v-else class="video-unavailable">Prévia indisponível</div>
          </div>
          <div class="player-subcaption" v-if="current">
            <span>Formato vertical 9:16 com enquadramento inteligente e legendas ativas</span>
          </div>
        </aside>

        <!-- CARD INDICATIVO SE APENAS HOUVER PRÉVIAS EM GERAÇÃO (AINDA SEM PRÉVIAS PRONTAS) -->
        <aside
          v-else-if="visibleGeneration.length"
          class="cuts-player-rail"
          aria-label="Aguardando renderização"
        >
          <div class="clip-preview clip-preview-generating">
            <div class="generating-rail-card">
              <LoaderCircle class="spin" :size="32" />
              <h4>Renderizando cortes</h4>
              <p>
                Seus vídeos com enquadramento vertical 9:16 e legendas dinâmicas estão em produção.
              </p>
              <span class="subtle"
                >Assim que a primeira prévia estiver pronta, ela aparecerá aqui para você assistir e
                aprovar.</span
              >
            </div>
          </div>
        </aside>
      </div>
    </el-splitter-panel>
  </el-splitter>
</template>

<style scoped>
.cuts-review-layout {
  height: 600px !important;
  min-height: 520px !important;
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
  width: 1px !important;
  transition:
    background 0.15s ease,
    width 0.15s ease;
}

:deep(.el-splitter__bar:hover) {
  background: var(--color-accent, #d97724);
  width: 3px !important;
}

.panel-inner-container {
  height: 100%;
  width: 100%;
  padding: 16px;
  overflow-y: auto;
  box-sizing: border-box;
}

.player-rail-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.15);
}

.cuts-review-left-panel,
.cuts-player-rail-panel {
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  height: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.cuts-review-left {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.cuts-filters {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.cuts-filter-chip {
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 0.82rem;
  font-weight: 500;
}

.cuts-trash {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
}

.review-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.cuts-table-section {
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  padding: 0 !important;
}

.cuts-table-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.table-heading-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-primary, var(--ink));
}

.table-heading-title h3 {
  font-size: 0.95rem;
  margin: 0;
}

.cuts-table-scroll {
  max-height: 280px;
  overflow-y: auto;
  border-radius: 8px;
}

.clip-information {
  background: transparent !important;
  border: none !important;
  border-top: 1px solid var(--color-border-subtle, var(--line)) !important;
  border-radius: 0 !important;
  padding: 16px 0 0 0 !important;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.clip-info-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.delete-blocked-text {
  font-size: 0.77rem;
  color: var(--color-warning-text, #f59e0b);
  margin: 0;
}

.preview-label {
  font-size: 1.15rem;
  font-weight: 600;
  line-height: 1.3;
  margin: 0;
  color: var(--color-text-primary, var(--ink));
}

.clip-meta-strip {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.meta-tag {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.77rem;
  background: var(--color-surface-hover, var(--soft));
  padding: 3px 8px;
  border-radius: 6px;
  color: var(--color-text-secondary, var(--muted));
}

.cut-decision-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 4px 0;
  background: transparent;
  border: none;
  margin-top: 2px;
}

.decision-heading {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-text-primary, var(--ink));
}

.decision-btn-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.decision-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
  font-weight: 500;
  border-radius: 7px;
  transition: all 0.15s ease;
}

.decision-btn.approve-btn.active {
  background: var(--color-success-soft, rgba(16, 185, 129, 0.16));
  color: var(--color-success-text, #34d399);
  border-color: var(--color-success-border, rgba(16, 185, 129, 0.35));
  font-weight: 600;
}

.decision-btn.reject-btn.active {
  background: var(--color-danger-soft, rgba(239, 68, 68, 0.16));
  color: var(--color-danger-text, #f87171);
  border-color: var(--color-danger-border, rgba(239, 68, 68, 0.35));
  font-weight: 600;
}

.clip-copy {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 4px;
}

.copy-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.copy-header-row h3 {
  font-size: 0.85rem;
  font-weight: 600;
  margin: 0;
  color: var(--color-text-primary, var(--ink));
}

.description-box {
  background: rgba(255, 255, 255, 0.02);
  border: none;
  border-left: 2px solid var(--color-accent, #d97724);
  border-radius: 0 6px 6px 0;
  padding: 8px 14px;
  font-size: 0.82rem;
  line-height: 1.5;
  color: var(--color-text-secondary, var(--muted));
  max-height: 140px;
  overflow-y: auto;
}

.download-action-box {
  margin-top: 6px;
}

.download-main-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  padding: 10px 20px;
  text-decoration: none;
}

.cuts-player-rail {
  position: sticky;
  top: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
}

.clip-preview {
  width: 100%;
  aspect-ratio: 9/16;
  max-height: 480px;
  border-radius: 14px;
  overflow: hidden;
  background: #000;
  border: 1px solid var(--color-border-subtle, var(--line));
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
}

.clip-preview video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.player-subcaption {
  font-size: 0.72rem;
  color: var(--color-text-muted, var(--muted));
  text-align: center;
  padding: 0 8px;
}

@media (max-width: 950px) {
  .cuts-review-layout {
    grid-template-columns: 1fr;
  }
  .cuts-player-rail {
    position: static;
    max-width: 320px;
    margin: 0 auto;
  }
}

.render-resume-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: var(--color-warning-soft, rgba(245, 158, 11, 0.12));
  border: 1px solid var(--color-warning-border, rgba(245, 158, 11, 0.35));
  border-radius: 9px;
  padding: 10px 14px;
  font-size: 0.82rem;
  color: var(--color-warning-text, #fbbf24);
  margin-bottom: 16px;
}

.clip-item-generating {
  background: rgba(255, 255, 255, 0.02);
}

.clip-item-generating[data-state='running'] {
  background: rgba(217, 119, 36, 0.05);
}

.clip-item-generating[data-state='failed'] {
  background: rgba(239, 68, 68, 0.05);
}

.item-state-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-text-muted, var(--muted));
}

.item-state-dot[data-state='running'] {
  background: var(--color-primary, #d97706);
  box-shadow: 0 0 6px rgba(217, 119, 36, 0.6);
  animation: pulse 1.6s infinite ease-in-out;
}

.item-state-dot[data-state='failed'] {
  background: var(--color-danger, #ef4444);
}

.generating-title-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.generating-error-snippet {
  color: var(--color-danger-text, #f87171);
  font-size: 0.74rem;
  line-height: 1.3;
}

.row-progress-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 100px;
}

.row-progress-bar {
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: var(--color-surface-hover, var(--soft));
  overflow: hidden;
}

.row-progress-bar span {
  display: block;
  height: 100%;
  background: var(--color-primary, #d97706);
  border-radius: 999px;
  transition: width 0.3s ease;
}

.subtle-time,
.subtle-phase {
  font-size: 0.78rem;
  color: var(--color-text-secondary, var(--muted));
}

.generating-status-action {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.retry-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.74rem;
  padding: 3px 8px;
  border-radius: 6px;
  color: var(--color-danger-text, #f87171);
  border-color: rgba(239, 68, 68, 0.3);
}

.retry-btn:hover {
  background: rgba(239, 68, 68, 0.15);
}

.clip-preview-generating {
  padding: 24px;
  background: var(--color-surface, var(--panel));
}

.generating-rail-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 10px;
  color: var(--color-text-primary, var(--ink));
}

.generating-rail-card h4 {
  margin: 0;
  font-size: 1rem;
}

.generating-rail-card p {
  margin: 0;
  font-size: 0.8rem;
  color: var(--color-text-secondary, var(--muted));
  line-height: 1.4;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(0.9);
  }
}
</style>
