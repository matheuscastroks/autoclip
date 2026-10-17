<script setup lang="ts">
import { computed, ref, onBeforeUnmount, watch, nextTick } from 'vue';
import type { Transcript } from '../types';
import { time } from '../format';
import { vRecoverMedia } from '../directives/recoverMedia';
import { api } from '../api';
import { notify } from '../notifications';
import AppIcon from './ui/AppIcon.vue';
import AppButton from './AppButton.vue';

const props = defineProps<{
  projectId?: string;
  transcript: Transcript | null;
  sourceUrl: string;
  wordCount: number;
}>();

const emit = defineEmits<{
  'update:transcript': [value: Transcript];
  'save': [value: Transcript];
}>();

const query = defineModel<string>('query', { default: '' });
const player = ref<HTMLVideoElement>();
const passageList = ref<HTMLElement>();
const positionUs = ref(0);
const mediaError = ref('');
const followPauseTimer = ref<ReturnType<typeof setTimeout>>();
let followPaused = false;

// Editing state
const editingSegmentId = ref<string | null>(null);
const editingText = ref('');
const saving = ref(false);
const editorTextarea = ref<HTMLTextAreaElement>();

function startEdit(segment: { id: string; text: string }) {
  editingSegmentId.value = segment.id;
  editingText.value = segment.text;
  followPaused = true;
  nextTick(() => {
    if (editorTextarea.value && typeof editorTextarea.value.focus === 'function') {
      editorTextarea.value.focus();
    }
    if (editorTextarea.value && typeof editorTextarea.value.select === 'function') {
      editorTextarea.value.select();
    }
  });
}

function cancelEdit() {
  editingSegmentId.value = null;
  editingText.value = '';
}

async function saveEdit(segmentId: string) {
  const newText = editingText.value.trim();
  if (!newText) {
    notify.error('O texto da legenda não pode ficar vazio.');
    return;
  }
  
  if (props.projectId) {
    try {
      saving.value = true;
      const updated = await api.updateTranscript(props.projectId, {
        segments: [{ id: segmentId, text: newText }],
      });
      emit('update:transcript', updated);
      emit('save', updated);
      notify.success('Legenda atualizada com sucesso.');
      editingSegmentId.value = null;
    } catch (err: unknown) {
      notify.error(err instanceof Error ? err.message : 'Falha ao salvar legenda.');
    } finally {
      saving.value = false;
    }
  } else {
    // When used in test/isolated props mode
    if (props.transcript) {
      const seg = props.transcript.segments.find(s => s.id === segmentId);
      if (seg) seg.text = newText;
    }
    emit('update:transcript', props.transcript!);
    emit('save', props.transcript!);
    editingSegmentId.value = null;
  }
}
const segments = computed(() =>
  props.transcript?.segments.length
    ? props.transcript.segments
    : props.transcript?.words.reduce<Transcript['segments']>((all, word, index) => {
        if (index % 12 === 0)
          all.push({ id: word.id, text: word.text, start_us: word.start_us, end_us: word.end_us });
        else {
          all[all.length - 1].text += ' ' + word.text;
          all[all.length - 1].end_us = word.end_us;
        }
        return all;
      }, []) || []
);
const filtered = computed(() =>
  segments.value.filter(s =>
    s.text.toLocaleLowerCase('pt-BR').includes(query.value.trim().toLocaleLowerCase('pt-BR'))
  )
);
const activeSegmentId = computed(
  () =>
    filtered.value.find(s => positionUs.value >= s.start_us && positionUs.value < s.end_us)?.id ||
    ''
);
const escapeSelector = (val: string) =>
  typeof CSS !== 'undefined' && CSS.escape ? CSS.escape(val) : val.replace(/["\\]/g, '\\$&');

watch(activeSegmentId, async id => {
  if (!id || followPaused) return;
  await Promise.resolve();
  passageList.value
    ?.querySelector<HTMLElement>(`[data-segment="${escapeSelector(id)}"]`)
    ?.scrollIntoView?.({ block: 'nearest', behavior: 'smooth' });
});
function pauseFollow() {
  followPaused = true;
  if (followPauseTimer.value) clearTimeout(followPauseTimer.value);
  followPauseTimer.value = setTimeout(() => {
    followPaused = false;
    const id = activeSegmentId.value;
    if (id)
      passageList.value
        ?.querySelector<HTMLElement>(`[data-segment="${escapeSelector(id)}"]`)
        ?.scrollIntoView?.({ block: 'nearest' });
  }, 4000);
}
async function seek(us: number) {
  if (!player.value) return;
  player.value.currentTime = us / 1e6;
  positionUs.value = us;
  mediaError.value = '';
  try {
    await player.value.play();
  } catch {
    mediaError.value =
      'Não foi possível iniciar a reprodução. Use os controles do vídeo para tentar novamente.';
  }
}
function seekUnlessSelectingText(us: number) {
  if (window.getSelection()?.toString()) return;
  void seek(us);
}
function release() {
  if (!player.value) return;
  player.value.pause();
  player.value.removeAttribute('src');
  player.value.load();
}
watch(
  () => props.transcript,
  value => {
    if (!value) release();
  },
  { flush: 'sync' }
);
onBeforeUnmount(release);
onBeforeUnmount(() => {
  if (followPauseTimer.value) clearTimeout(followPauseTimer.value);
});
</script>
<template>
  <section class="transcript-panel" aria-label="Consulta da transcrição">
    <header class="transcript-panel-header">
      <div>
        <h2>Transcrição original</h2>
        <p>
          {{ wordCount.toLocaleString('pt-BR') }} palavras · Consulta opcional para conferir o
          contexto
        </p>
      </div>
      <label class="transcript-query"
        ><AppIcon name="search" size="sm" /><input
          v-model="query"
          type="search"
          placeholder="Buscar termos na fala..."
          aria-label="Buscar na transcrição"
      /></label>
    </header>
    <div v-if="transcript" class="transcript-panel-regions">
      <section class="transcript-original" aria-label="Vídeo original">
        <video
          v-if="sourceUrl"
          ref="player"
          v-recover-media="sourceUrl"
          :src="sourceUrl"
          controls
          preload="metadata"
          playsinline
          aria-label="Original transcrito"
          @timeupdate="positionUs = (player?.currentTime || 0) * 1e6"
          @loadedmetadata="mediaError = ''"
        />
        <p v-else>Vídeo indisponível. A transcrição permanece disponível para consulta.</p>
        <p v-if="mediaError" role="alert">{{ mediaError }}</p>
        <small
          >Use os timestamps para reproduzir o trecho. O texto pode ser selecionado e
          copiado.</small
        >
      </section>
      <section
        ref="passageList"
        class="transcript-passages"
        tabindex="0"
        aria-label="Segmentos da transcrição"
        @wheel.passive="pauseFollow"
        @touchmove.passive="pauseFollow"
      >
        <button
          v-for="segment in filtered"
          :key="segment.id"
          type="button"
          class="transcript-segment-row"
          :class="{
            current: positionUs >= segment.start_us && positionUs < segment.end_us,
            editing: editingSegmentId === segment.id,
          }"
          :aria-current="
            positionUs >= segment.start_us && positionUs < segment.end_us ? 'true' : undefined
          "
          :data-segment="segment.id"
          :disabled="!sourceUrl"
          :aria-label="'Reproduzir trecho iniciado em ' + time(segment.start_us)"
          @click="editingSegmentId !== segment.id && seekUnlessSelectingText(segment.start_us)"
        >
          <time>{{ time(segment.start_us) }}</time>

          <!-- Normal Display Mode -->
          <div v-if="editingSegmentId !== segment.id" class="segment-display-wrap">
            <p>{{ segment.text }}</p>
            <span
              role="button"
              tabindex="0"
              class="edit-segment-btn"
              data-action="edit-segment"
              title="Editar legenda deste trecho"
              aria-label="Editar legenda deste trecho"
              @click.stop="startEdit(segment)"
              @keydown.enter.stop="startEdit(segment)"
            >
              <AppIcon name="pencil" size="sm" />
            </span>
          </div>

          <!-- Inline Edit Mode -->
          <div v-else class="segment-editor-wrap" @click.stop>
            <textarea
              ref="editorTextarea"
              v-model="editingText"
              class="segment-editor-input"
              rows="2"
              aria-label="Texto corrigido da legenda"
              :disabled="saving"
              @keydown.enter.exact.prevent="saveEdit(segment.id)"
              @keydown.esc.stop="cancelEdit"
            />
            <div class="segment-editor-actions">
              <AppButton
                class="button primary small"
                data-action="save-segment"
                :loading="saving"
                :disabled="saving"
                @click.stop="saveEdit(segment.id)"
              >
                Salvar
              </AppButton>
              <AppButton
                class="button secondary small"
                data-action="cancel-segment"
                :disabled="saving"
                @click.stop="cancelEdit"
              >
                Cancelar
              </AppButton>
            </div>
          </div>
        </button>
        <p v-if="!filtered.length" class="transcript-empty">
          {{
            query
              ? 'Nenhum trecho corresponde à busca. Ajuste o termo para continuar.'
              : 'A transcrição não contém trechos disponíveis.'
          }}
        </p>
      </section>
    </div>
    <section v-else class="transcript-empty">
      <h3>Ainda sem transcrição</h3>
      <p>
        Inicie ou recupere a transcrição na aba Preparação. Não é necessário aprovar esta consulta
        para gerar cortes.
      </p>
    </section>
  </section>
</template>
<style scoped>
.transcript-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-height: 0;
  min-width: 0;
  height: 100%;
}
.transcript-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
h2 {
  font-size: var(--font-size-region);
}
.transcript-panel-header p,
small {
  color: var(--color-text-secondary);
  font-size: var(--font-size-meta);
}
.transcript-query {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 6px 10px;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-control);
}
.transcript-query:focus-within {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 2px;
}
.transcript-query input {
  min-width: 0;
  background: transparent;
  color: var(--color-text-primary);
  border: 0;
}
.transcript-panel-regions {
  display: grid;
  grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.2fr);
  gap: 24px;
  min-height: 0;
  flex: 1;
}
.transcript-original {
  min-width: 0;
  overflow: auto;
}
.transcript-original video {
  display: block;
  width: 100%;
  aspect-ratio: 16/9;
  background: var(--color-canvas);
  max-height: 420px;
}
.transcript-original small {
  display: block;
  margin-top: 12px;
}
.transcript-passages {
  overflow: auto;
  min-width: 0;
  min-height: 0;
}
.transcript-segment-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  width: 100%;
  gap: 16px;
  padding: 12px;
  border: 0;
  border-bottom: 1px solid var(--color-border-subtle);
  background: transparent;
  border-radius: 0;
  color: var(--color-text-primary);
  font: inherit;
  text-align: left;
  cursor: pointer;
  user-select: text;
}
.transcript-segment-row.current {
  background: var(--color-surface-selected);
}
.transcript-segment-row time {
  align-self: start;
  color: var(--color-action-primary);
  font-size: var(--font-size-meta);
  cursor: pointer;
  padding: 2px 4px;
  border-radius: var(--radius-subtle, 4px);
  user-select: none;
}
.transcript-segment-row time:hover {
  text-decoration: underline;
  background: var(--color-surface-hover);
}
.transcript-segment-row:disabled {
  cursor: default;
}
.segment-display-wrap {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
}
.segment-display-wrap p {
  user-select: text;
  margin: 0;
  font-size: var(--font-size-body);
  overflow-wrap: anywhere;
  flex: 1;
}
.edit-segment-btn {
  opacity: 0;
  background: transparent;
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-control);
  color: var(--color-text-secondary);
  padding: 4px 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.15s ease, background 0.15s ease, color 0.15s ease;
  flex-shrink: 0;
}
.transcript-segment-row:hover .edit-segment-btn,
.transcript-segment-row:focus-within .edit-segment-btn {
  opacity: 1;
}
.edit-segment-btn:hover {
  background: var(--color-surface-raised);
  color: var(--color-action-primary);
  border-color: var(--color-border-strong);
}
.segment-editor-wrap {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}
.segment-editor-input {
  width: 100%;
  padding: 8px 10px;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-control);
  color: var(--color-text-primary);
  font: inherit;
  font-size: var(--font-size-body);
  line-height: 1.5;
  resize: vertical;
  min-height: 60px;
  outline: none;
  box-shadow: 0 0 0 2px rgba(175, 198, 213, 0.2);
}
.segment-editor-input:focus {
  border-color: var(--color-action-primary);
  box-shadow: 0 0 0 2px rgba(175, 198, 213, 0.35);
}
.segment-editor-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.transcript-empty {
  padding: 24px 0;
  color: var(--color-text-secondary);
}
.transcript-empty h3 {
  color: var(--color-text-primary);
  font-size: var(--font-size-region);
  margin-bottom: 8px;
}
@media (max-width: 1050px) {
  .transcript-panel {
    gap: 16px;
  }
  .transcript-panel-regions {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: auto minmax(0, 1fr);
    gap: 16px;
  }
  .transcript-original video {
    max-height: 190px;
  }
  .transcript-original small {
    margin-top: 4px;
  }
}
</style>
