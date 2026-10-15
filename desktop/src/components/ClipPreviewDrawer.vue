<script setup lang="ts">
import { computed, ref, watch, onBeforeUnmount } from 'vue';
import { ElDrawer } from 'element-plus';
import AppButton from './AppButton.vue';
import { vRecoverMedia } from '../directives/recoverMedia';
import { active, labels, time } from '../format';
import type { Revision, Job, Decision, Checks } from '../types';
import { isFinalAvailable, isExportable } from '../domain/revisionPresentation';

const props = defineProps<{
  modelValue: boolean;
  revision?: Revision;
  loadMedia?: (asset: string) => Promise<string>;
  mediaUrl?: string;
  sourceUrl?: string;
  jobs?: Job[];
  busy?: boolean;
  deleteBlockedReason?: string;
}>();
const emit = defineEmits<{
  'update:modelValue': [value: boolean];
  renderFinal: [id: string];
  cancel: [id: string];
  resume: [id: string];
  decision: [value: Decision];
  delete: [id: string];
  export: [];
}>();
const version = ref<'preview' | 'final' | 'source'>('preview');
const url = ref('');
const loading = ref(false);
const error = ref('');
const player = ref<HTMLVideoElement>();
const closing = ref(false);
let request = 0;
const hasPreview = computed(() => props.revision?.preview?.state === 'available');
const hasFinal = computed(() => !!props.revision && isFinalAvailable(props.revision));
const finalJob = computed(() =>
  [...(props.jobs || [])]
    .sort((a, b) => b.created_at.localeCompare(a.created_at))
    .find(
      j =>
        j.operation === 'render_final' &&
        j.progress?.items?.some(i => i.revision_id === props.revision?.revision_id)
    )
);
const finalRunning = computed(() => !!finalJob.value && active(finalJob.value.status));
const finalItem = computed(() =>
  finalJob.value?.progress?.items?.find(i => i.revision_id === props.revision?.revision_id)
);
const criteria: { key: keyof Checks; label: string }[] = [
  { key: 'completeness', label: 'O pensamento está completo' },
  { key: 'context', label: 'O trecho funciona fora do vídeo original' },
  { key: 'qualifications', label: 'Negações, números e ressalvas foram preservados' },
  { key: 'words_and_boundaries', label: 'Nenhuma palavra ou argumento foi cortado' },
  { key: 'audiovisual', label: 'Áudio, quadro e legendas foram revisados' },
];
const emptyChecks = (): Checks => ({
  completeness: false,
  context: false,
  qualifications: false,
  words_and_boundaries: false,
  audiovisual: false,
});
const checks = ref<Checks>(emptyChecks());
const canReview = computed(
  () =>
    version.value === 'final' &&
    hasFinal.value &&
    props.revision?.technical_pass &&
    !!props.revision.content_hash &&
    !finalRunning.value
);
const confirmed = computed(() => criteria.every(c => checks.value[c.key]));
const title = computed(() =>
  version.value === 'source'
    ? 'Original com contexto'
    : version.value === 'preview'
      ? 'Prévia rápida · 540 × 960'
      : 'Versão final · 1080 × 1920'
);

function releasePlayer() {
  if (!player.value) return;
  player.value.pause();
  player.value.removeAttribute('src');
  player.value.load();
}
function close() {
  closing.value = true;
  ++request;
  releasePlayer();
  url.value = '';
  loading.value = false;
  emit('update:modelValue', false);
}
function beforeClose(done: () => void) {
  close();
  done();
}
async function load() {
  const current = ++request;
  releasePlayer();
  url.value = '';
  error.value = '';
  if (!props.modelValue || closing.value || !props.revision) {
    loading.value = false;
    return;
  }
  loading.value = true;
  try {
    const asset =
      version.value === 'preview' ? props.revision.preview?.asset : props.revision.revision_id;
    const next =
      version.value === 'source'
        ? props.sourceUrl || ''
        : props.loadMedia && asset
          ? await props.loadMedia(asset)
          : props.mediaUrl || '';
    if (current !== request) return;
    if (!next) throw new Error('Vídeo indisponível. Tente carregar novamente.');
    url.value = next;
  } catch (e) {
    if (current === request) error.value = (e as Error).message;
  } finally {
    if (current === request) loading.value = false;
  }
}
watch(
  [() => props.modelValue, () => props.revision?.revision_id],
  () => {
    if (props.modelValue) closing.value = false;
    version.value = hasPreview.value ? 'preview' : 'final';
    checks.value = emptyChecks();
  },
  { immediate: true, flush: 'sync' }
);
watch(
  [
    () => props.modelValue,
    () => props.revision?.revision_id,
    () => props.revision?.content_hash,
    version,
    () => props.mediaUrl,
  ],
  load,
  { immediate: true }
);
watch(
  [() => props.revision?.revision_id, () => props.revision?.content_hash, () => props.modelValue],
  () => {
    checks.value = emptyChecks();
  }
);
function metadata() {
  error.value = '';
  if (version.value === 'source' && player.value)
    player.value.currentTime = Math.max(0, (props.revision?.start_us || 0) / 1e6 - 30);
}
function decide(decision: 'approved' | 'rejected') {
  if (!props.revision || !canReview.value || (decision === 'approved' && !confirmed.value)) return;
  emit('decision', {
    revision_id: props.revision.revision_id,
    decision,
    checks: { ...checks.value },
    notes: '',
    content_hash: props.revision.content_hash || '',
  });
}
onBeforeUnmount(() => {
  ++request;
  releasePlayer();
});
</script>

<template>
  <ElDrawer
    :model-value="modelValue"
    :title="revision?.title || 'Visualizar corte'"
    direction="rtl"
    size="62%"
    class="clip-preview-drawer"
    destroy-on-close
    :before-close="beforeClose"
    @update:model-value="$emit('update:modelValue', $event)"
    @close="close"
  >
    <template #header="{ titleId }">
      <div class="clip-drawer-heading">
        <h2 :id="titleId" class="preview-label">{{ revision?.title || 'Visualizar corte' }}</h2>
        <p>
          {{ time(revision?.duration_us) }} ·
          {{
            finalRunning
              ? 'Versão final em processamento'
              : hasFinal
                ? labels[revision?.review_status || '']
                : 'Prévia disponível · final ainda não gerada'
          }}
        </p>
      </div>
    </template>
    <div v-if="modelValue && !closing && revision" class="clip-drawer-content clip-information">
      <div class="clip-version-tabs" aria-label="Versão do vídeo">
        <button
          v-if="hasPreview"
          type="button"
          data-version="preview"
          :aria-pressed="version === 'preview'"
          @click="version = 'preview'"
        >
          Prévia
        </button>
        <button
          v-if="hasFinal"
          type="button"
          data-version="final"
          :aria-pressed="version === 'final'"
          @click="version = 'final'"
        >
          Final
        </button>
        <button
          v-if="sourceUrl"
          type="button"
          data-version="source"
          :aria-pressed="version === 'source'"
          @click="version = 'source'"
        >
          Original com contexto
        </button>
      </div>
      <p class="clip-version-label">{{ title }}</p>
      <div class="clip-inspection-grid">
        <div class="clip-player-column">
          <div
            class="clip-preview"
            :class="{ 'original-preview': version === 'source' }"
            :aria-busy="loading"
          >
            <video
              v-if="url"
              :key="revision.revision_id + version"
              ref="player"
              v-recover-media="url"
              :src="url"
              controls
              preload="metadata"
              playsinline
              @loadedmetadata="metadata"
              @error="
                error =
                  'Falha na reprodução. O acesso será renovado; você também pode tentar novamente.'
              "
            />
            <p v-else>{{ loading ? 'Carregando vídeo…' : 'Vídeo indisponível' }}</p>
          </div>
          <div v-if="error" class="clip-media-error" role="alert">
            <p>{{ error }}</p>
            <AppButton data-action="retry-media" :disabled="loading" @click="load"
              >Tentar novamente</AppButton
            >
          </div>
        </div>
        <div class="clip-inspection-details">
          <div v-if="finalRunning" class="clip-processing" role="status">
            <strong>{{
              finalItem?.phase === 'verify'
                ? 'Validando versão final'
                : finalJob?.status === 'pending'
                  ? 'Versão final na fila'
                  : 'Renderizando versão final'
            }}</strong>
            <progress
              v-if="finalItem?.total_us"
              :value="finalItem.processed_us"
              :max="finalItem.total_us"
            />
            <p>A prévia continua disponível. A aprovação será liberada após a validação final.</p>
          </div>
          <details>
            <summary>Detalhes do corte</summary>
            <dl>
              <dt>Intervalo original</dt>
              <dd>{{ time(revision.start_us) }} – {{ time(revision.end_us) }}</dd>
              <dt>Duração editada</dt>
              <dd>{{ time(revision.duration_us) }}</dd>
              <dt>Silêncios removidos</dt>
              <dd>{{ time(revision.removed_silence_us) }}</dd>
            </dl>
            <p v-if="revision.opening_text">
              <strong>Título de abertura</strong><br />{{ revision.opening_text }}
            </p>
            <p v-if="revision.rationale">{{ revision.rationale }}</p>
          </details>
          <details>
            <summary>Descrição para publicação</summary>
            <p class="publication-copy">
              {{ revision.description || 'Sem descrição gerada para este corte.' }}
            </p>
          </details>
          <details v-if="revision.warnings.length">
            <summary>Avisos ({{ revision.warnings.length }})</summary>
            <ul>
              <li v-for="(warning, index) in revision.warnings" :key="index">{{ warning }}</li>
            </ul>
          </details>
          <fieldset v-if="canReview" class="editorial-checklist">
            <legend>Confirme após assistir ao original com contexto e ao corte completo</legend>
            <label v-for="criterion in criteria" :key="criterion.key"
              ><input v-model="checks[criterion.key]" type="checkbox" />{{ criterion.label }}</label
            >
          </fieldset>
          <p v-else class="clip-review-note">
            A prévia rápida não aprova a versão final. A revisão editorial exige o arquivo final
            tecnicamente válido.
          </p>
          <p v-if="deleteBlockedReason" id="delete-blocked-reason">{{ deleteBlockedReason }}</p>
        </div>
      </div>
    </div>
    <template #footer>
      <div v-if="revision" class="clip-drawer-actions">
        <AppButton
          data-action="delete-clip"
          :disabled="busy || !!deleteBlockedReason"
          :title="deleteBlockedReason || 'Mover corte para a lixeira'"
          @click="$emit('delete', revision.revision_id)"
          >Excluir corte</AppButton
        >
        <AppButton
          v-if="finalRunning && finalJob"
          :disabled="busy || finalJob.status === 'cancelling'"
          @click="$emit('cancel', finalJob.id)"
          >Cancelar render final</AppButton
        >
        <AppButton
          v-else-if="
            !hasFinal &&
            finalJob &&
            ['failed', 'cancelled', 'interrupted'].includes(finalJob.status)
          "
          :disabled="busy"
          @click="$emit('resume', finalJob.id)"
          >Retomar versão final</AppButton
        >
        <AppButton
          v-else-if="!hasFinal && revision.can_render_final"
          data-action="render-final"
          class="button primary"
          :disabled="busy"
          @click="$emit('renderFinal', revision.revision_id)"
          >Gerar versão final</AppButton
        >
        <template v-if="canReview">
          <AppButton data-action="editorial-reject" :disabled="busy" @click="decide('rejected')"
            >Rejeitar</AppButton
          >
          <AppButton
            data-action="editorial-approve"
            :disabled="busy || !confirmed"
            @click="decide('approved')"
            >{{
              revision.review_status === 'approved' ? 'Aprovado para publicação' : 'Aprovar corte'
            }}</AppButton
          >
        </template>
        <a
          v-if="hasFinal && revision.technical_pass && version === 'final' && url && !error"
          class="button secondary"
          :href="url + (url.includes('?') ? '&' : '?') + 'download=1'"
          download
          >Baixar final técnico</a
        >
        <AppButton
          v-if="isExportable(revision)"
          :disabled="busy || finalRunning"
          @click="$emit('export')"
          >Exportar aprovados</AppButton
        >
        <AppButton data-action="close-preview" @click="close">Fechar</AppButton>
      </div>
    </template>
  </ElDrawer>
</template>

<style>
.clip-preview-drawer {
  background: var(--panel);
  max-width: 100vw;
}
.clip-preview-drawer .el-drawer__header {
  margin: 0;
  padding: 20px 24px;
  border-bottom: 1px solid var(--line);
}
.clip-preview-drawer .el-drawer__body {
  padding: 20px 24px;
  min-height: 0;
  overflow: auto;
}
.clip-preview-drawer .el-drawer__footer {
  padding: 16px 24px;
  border-top: 1px solid var(--line);
}
.clip-drawer-heading {
  min-width: 0;
}
.clip-drawer-heading h2 {
  font-size: 17px;
  line-height: 1.4;
  margin: 0;
  overflow-wrap: anywhere;
}
.clip-drawer-heading p,
.clip-version-label {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin: 8px 0 0;
}
.clip-version-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.clip-version-tabs button {
  padding: 8px 12px;
  background: transparent;
  border: 1px solid var(--line);
  border-radius: var(--radius-control);
  color: var(--muted);
  cursor: pointer;
}
.clip-version-tabs button[aria-pressed='true'] {
  background: var(--soft);
  color: var(--ink);
  border-color: var(--line-strong);
}
.clip-inspection-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 24px;
  margin-top: 20px;
}
.clip-player-column,
.clip-inspection-details {
  min-width: 0;
}
.clip-preview-drawer .clip-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  width: min(100%, 34.875vh);
  margin-inline: auto;
  aspect-ratio: 9/16;
  background: var(--canvas);
  border: 1px solid var(--line);
  border-radius: var(--radius-control);
  overflow: hidden;
}
.clip-preview-drawer .clip-preview video {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.clip-preview-drawer .clip-preview p {
  color: var(--muted);
  font-size: 12px;
  padding: 16px;
}
.clip-preview-drawer .original-preview {
  width: 100%;
  aspect-ratio: 16/9;
}
.clip-inspection-details {
  display: flex;
  flex-direction: column;
  gap: 16px;
  font-size: 12px;
  line-height: 1.6;
  overflow-wrap: anywhere;
}
.clip-inspection-details details {
  border-bottom: 1px solid var(--line);
  padding-bottom: 14px;
}
.clip-inspection-details summary {
  cursor: pointer;
  color: var(--ink);
  font-weight: 500;
}
.clip-inspection-details p,
.clip-inspection-details dd {
  color: var(--color-text-secondary);
}
.clip-inspection-details dl {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 0;
}
.clip-inspection-details dd {
  margin: 0;
  text-align: right;
}
.publication-copy {
  white-space: pre-line;
}
.clip-preview-drawer .editorial-checklist {
  display: grid;
  gap: 12px;
  border: 0;
  padding: 0;
  margin: 0;
}
.clip-preview-drawer .editorial-checklist legend {
  font-weight: 500;
  margin-bottom: 12px;
}
.clip-preview-drawer .editorial-checklist label {
  display: flex;
  align-items: start;
  gap: 8px;
}
.clip-processing progress {
  display: block;
  width: 100%;
  margin-top: 12px;
}
.clip-media-error {
  font-size: 12px;
  color: var(--color-warning-text);
}
.clip-drawer-actions {
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
}
.clip-drawer-actions .el-button + .el-button {
  margin-left: 0;
}
@media (max-width: 1100px) {
  .clip-preview-drawer {
    width: 100% !important;
  }
}
@media (max-width: 700px) {
  .clip-inspection-grid {
    grid-template-columns: 1fr;
  }
  .clip-preview-drawer .clip-preview {
    max-width: 300px;
    margin: auto;
  }
  .clip-preview-drawer .el-drawer__body {
    padding: 16px;
  }
}
</style>
