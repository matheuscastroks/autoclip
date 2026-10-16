<script setup lang="ts">
import { computed, ref, watch, onBeforeUnmount } from 'vue';
import { ElDrawer } from 'element-plus';
import type { Proposal } from '../../types';
import { time } from '../../format';
import AppButton from '../AppButton.vue';
import { vRecoverMedia } from '../../directives/recoverMedia';

const props = defineProps<{
  modelValue: boolean;
  proposal?: Proposal;
  sourceUrl: string;
  selected: boolean;
  discarded: boolean;
  overlapping: boolean;
  busy: boolean;
  analysisComplete: boolean;
  loadSource?: () => Promise<string>;
}>();
const emit = defineEmits<{
  'update:modelValue': [open: boolean];
  toggleSelection: [];
  discard: [];
  restore: [];
  restoreFocus: [];
}>();
let opener: HTMLElement | null = null;
function restoreFocus(event?: Event) {
  if (opener?.isConnected) return;
  event?.preventDefault();
  emit('restoreFocus');
}
const player = ref<HTMLVideoElement>();
const url = ref('');
const loading = ref(false);
const error = ref('');
const closing = ref(false);
const playEnd = ref(0);
let request = 0;
const canSelect = computed(
  () =>
    props.analysisComplete &&
    props.proposal?.eligible &&
    !props.busy &&
    !props.discarded &&
    (props.selected || !props.overlapping)
);
function release() {
  playEnd.value = 0;
  if (!player.value) return;
  player.value.pause();
  player.value.removeAttribute('src');
  player.value.load();
}
function close() {
  closing.value = true;
  ++request;
  release();
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
  release();
  url.value = '';
  error.value = '';
  if (!props.modelValue || closing.value || !props.proposal) {
    loading.value = false;
    return;
  }
  loading.value = true;
  try {
    const next = props.loadSource ? await props.loadSource() : props.sourceUrl;
    if (current !== request) return;
    if (!next)
      throw new Error(
        'Vídeo original indisponível. Você pode consultar o texto e tentar novamente.'
      );
    url.value = next;
  } catch (e) {
    if (current === request) error.value = (e as Error).message;
  } finally {
    if (current === request) loading.value = false;
  }
}
async function play(context = false) {
  if (!player.value || !props.proposal) return;
  const video = player.value;
  video.currentTime = Math.max(0, props.proposal.start_us / 1e6 - (context ? 15 : 0));
  playEnd.value = props.proposal.end_us / 1e6 + (context ? 15 : 0);
  try {
    await video.play();
  } catch {
    error.value = 'Não foi possível iniciar a reprodução. Tente novamente.';
  }
}
function stopAtEnd() {
  if (player.value && playEnd.value && player.value.currentTime >= playEnd.value) {
    player.value.pause();
    playEnd.value = 0;
  }
}
watch(
  () => props.modelValue,
  open => {
    if (open) {
      closing.value = false;
      opener = document.activeElement as HTMLElement | null;
    }
  },
  { flush: 'sync', immediate: true }
);
watch([() => props.modelValue, () => props.proposal?.candidate_id, () => props.sourceUrl], load, {
  immediate: true,
});
onBeforeUnmount(() => {
  ++request;
  release();
});
</script>
<template>
  <ElDrawer
    :model-value="modelValue"
    :title="proposal?.title || 'Examinar proposta'"
    direction="rtl"
    size="60%"
    class="proposal-inspector-drawer"
    destroy-on-close
    :before-close="beforeClose"
    @close-auto-focus="restoreFocus"
    @close="close"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <template #header="{ titleId }"
      ><div class="inspector-heading">
        <h2 :id="titleId">{{ proposal?.title }}</h2>
        <p>
          {{ time(proposal?.start_us) }} – {{ time(proposal?.end_us) }} ·
          {{ time(proposal?.duration_us) }}
        </p>
      </div></template
    >
    <section
      v-if="modelValue && !closing && proposal"
      class="proposal-detail proposal-inspector-body"
    >
      <div class="inspector-media" :aria-busy="loading">
        <video
          v-if="url"
          ref="player"
          v-recover-media="url"
          :src="url"
          controls
          preload="metadata"
          playsinline
          aria-label="Original da proposta"
          @timeupdate="stopAtEnd"
        />
        <p v-if="loading" role="status">Carregando vídeo original…</p>
        <p v-if="error" role="alert">{{ error }}</p>
        <AppButton
          v-if="error"
          class="button secondary"
          data-action="retry-proposal-media"
          @click="load"
          >Tentar novamente</AppButton
        >
        <div class="inspector-play-actions">
          <AppButton
            class="button secondary"
            :disabled="!url"
            data-action="play-proposal"
            @click="play()"
            >Ouvir trecho</AppButton
          ><AppButton
            class="button secondary"
            :disabled="!url"
            data-action="play-context"
            @click="play(true)"
            >Contexto (±15s)</AppButton
          >
        </div>
      </div>
      <div class="opening-copy">
        <div class="opening-header">
          <span class="opening-badge">Frase de abertura · Primeiros 7 segundos</span>
        </div>
        <p class="opening-quote">{{ proposal.opening_text || 'Nenhuma frase de abertura sugerida.' }}</p>
      </div>
      <section class="editorial-section">
        <div class="editorial-header">
          <h4>Justificativa editorial</h4>
        </div>
        <p class="rationale-text">{{ proposal.rationale }}</p>
        <div class="criteria-card">
          <div class="criteria-card-title">Critérios editoriais</div>
          <dl class="inspector-criteria">
            <template
              v-for="(label, key) in {
                completeness: 'Raciocínio completo',
                standalone_context: 'Contexto suficiente',
                qualification_preserved: 'Ressalvas preservadas',
              }"
              :key="key"
            >
              <dt>{{ label }}</dt>
              <dd>
                <span
                  class="criterion-pill"
                  :class="{
                    'pill-yes': proposal.editorial[key] === 'yes',
                    'pill-no': proposal.editorial[key] === 'no',
                    'pill-uncertain': proposal.editorial[key] !== 'yes' && proposal.editorial[key] !== 'no',
                  }"
                >
                  <span class="pill-dot" aria-hidden="true"></span>
                  {{
                    proposal.editorial[key] === 'yes'
                      ? 'Sim'
                      : proposal.editorial[key] === 'no'
                        ? 'Não'
                        : 'Incerto'
                  }}
                </span>
              </dd>
            </template>
          </dl>
        </div>
      </section>
      <p v-if="!proposal.eligible" class="inspector-warning">
        Não elegível: {{ proposal.reasons.join(' ') }}
      </p>
      <p v-if="discarded" class="inspector-warning">
        Proposta descartada. Restaure para voltar a selecioná-la.
      </p>
      <p v-else-if="overlapping && !selected" class="inspector-warning">
        Este trecho se sobrepõe a um corte já selecionado. Desmarque o corte concorrente para
        selecioná-lo.
      </p>
      <details class="inspector-transcript" open>
        <summary>Fala e contexto original</summary>
        <p v-if="proposal.context_before" class="context-text">{{ proposal.context_before }}</p>
        <p>{{ proposal.text }}</p>
        <p v-if="proposal.context_after" class="context-text">{{ proposal.context_after }}</p>
      </details>
      <details v-if="proposal.warnings.length">
        <summary>Avisos editoriais ({{ proposal.warnings.length }})</summary>
        <p v-for="warning in proposal.warnings" :key="warning">{{ warning }}</p>
      </details>
      <small
        >{{ proposal.evidence_word_ids.length }} referência(s) à transcrição · Timestamps estimados
        pelo ASR</small
      >
    </section>
    <template #footer
      ><div v-if="proposal" class="inspector-footer">
        <AppButton
          class="button primary"
          data-action="select-focused"
          :disabled="!canSelect"
          @click="$emit('toggleSelection')"
          >{{ selected ? 'Remover da seleção' : 'Selecionar este trecho' }}</AppButton
        ><AppButton
          class="button secondary"
          :disabled="busy"
          :data-action="discarded ? 'restore-focused' : 'discard-focused'"
          @click="discarded ? $emit('restore') : $emit('discard')"
          >{{ discarded ? 'Restaurar proposta' : 'Descartar proposta' }}</AppButton
        ><AppButton class="button secondary" @click="close">Fechar</AppButton>
      </div></template
    >
  </ElDrawer>
</template>
<style>
.proposal-inspector-drawer.el-drawer {
  max-width: 100vw;
  background: var(--color-surface);
}
.proposal-inspector-drawer .el-drawer__body {
  min-height: 0;
  overflow: auto;
  padding: 0 24px 24px;
}
.proposal-inspector-drawer .el-drawer__footer {
  border-top: 1px solid var(--color-border-subtle);
  padding: 16px 24px;
}
@media (max-width: 1050px) {
  .proposal-inspector-drawer.el-drawer {
    width: 100% !important;
  }
}
</style>
<style scoped>
.inspector-heading {
  min-width: 0;
}
.inspector-heading h2 {
  font-size: var(--font-size-title);
  overflow-wrap: anywhere;
}
.inspector-heading p {
  color: var(--color-text-secondary);
  margin-top: 8px;
}
.proposal-inspector-body {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 0;
  overflow: visible;
  height: auto;
  border: 0;
  background: transparent;
  box-shadow: none;
}
.proposal-inspector-body h3 {
  font-size: var(--font-size-region);
}
.proposal-inspector-body h4,
summary {
  font-size: var(--font-size-body);
  font-weight: 600;
  margin-bottom: 8px;
}
.proposal-inspector-body p {
  max-width: 75ch;
  overflow-wrap: anywhere;
}
.inspector-media video {
  width: 100%;
  aspect-ratio: 16/9;
  max-height: 380px;
  object-fit: contain;
  background: var(--color-canvas);
}
.inspector-play-actions,
.inspector-footer {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.inspector-play-actions {
  margin-top: 12px;
}
.opening-copy {
  padding: 16px;
  background: var(--color-surface, #1e2227);
  border: 1px solid var(--color-border-subtle, rgba(255, 255, 255, 0.08));
  border-left: 3px solid var(--color-primary, #ffd700);
  border-radius: var(--radius-card, 8px);
}
.opening-header {
  margin-bottom: 8px;
}
.opening-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--color-primary, #ffd700);
}
.opening-quote {
  font-size: var(--font-size-body, 14px);
  line-height: 1.6;
  color: var(--ink, #fff);
  font-style: italic;
  margin: 0;
}
.editorial-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: var(--color-surface, #1e2227);
  border: 1px solid var(--color-border-subtle, rgba(255, 255, 255, 0.08));
  border-radius: var(--radius-card, 8px);
}
.editorial-header h4 {
  font-size: var(--font-size-body, 14px);
  font-weight: 600;
  color: var(--ink, #fff);
  margin: 0;
}
.rationale-text {
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-text-secondary, #d1d5db);
  margin: 0;
}
.criteria-card {
  margin-top: 6px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border-subtle, rgba(255, 255, 255, 0.08));
}
.criteria-card-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--color-text-secondary, #9ca3af);
  margin-bottom: 10px;
}
.inspector-criteria {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px 16px;
  margin: 0;
  font-size: var(--font-size-control, 13px);
}
.inspector-criteria dt {
  color: var(--ink, #e5e7eb);
  font-weight: 500;
}
.inspector-criteria dd {
  margin: 0;
  display: flex;
  justify-content: flex-end;
}
.criterion-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.4;
}
.pill-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.pill-yes {
  background: rgba(34, 197, 94, 0.12);
  color: #4ade80;
  border: 1px solid rgba(34, 197, 94, 0.25);
}
.pill-yes .pill-dot {
  background: #22c55e;
}
.pill-no {
  background: rgba(239, 68, 68, 0.12);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.25);
}
.pill-no .pill-dot {
  background: #ef4444;
}
.pill-uncertain {
  background: rgba(156, 163, 175, 0.12);
  color: #9ca3af;
  border: 1px solid rgba(156, 163, 175, 0.2);
}
.pill-uncertain .pill-dot {
  background: #9ca3af;
}
.context-text,
small {
  color: var(--color-text-secondary);
}
.inspector-transcript p {
  margin-top: 12px;
}
.inspector-warning {
  color: var(--color-warning-text);
}
</style>
