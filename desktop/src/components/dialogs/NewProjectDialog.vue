<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import AppButton from '../AppButton.vue';
import AppIcon from '../ui/AppIcon.vue';

export interface NewProjectInput {
  name: string;
  sourceInput: string;
  sourceKind: 'file' | 'url';
}
const open = defineModel<boolean>({ required: true });
const name = defineModel<string>('name', { required: true });
const sourceInput = defineModel<string>('sourceInput', { required: true });
const sourceKind = defineModel<'file' | 'url'>('sourceKind', { required: true });
const props = defineProps<{
  busy: boolean;
  picking?: boolean;
  setupReady: boolean;
  toolsAvailable: boolean;
  configSummary: string;
  error?: string;
}>();
const emit = defineEmits<{
  submit: [value: NewProjectInput];
  requestFilePicker: [];
  openSettings: [];
}>();
const dialog = ref<HTMLDialogElement>();
const validUrl = computed(() => {
  if (sourceKind.value !== 'url' || !sourceInput.value.trim()) return true;
  try {
    const url = new URL(sourceInput.value.trim());
    return (
      ['https:', 'http:'].includes(url.protocol) &&
      ['youtube.com', 'www.youtube.com', 'youtu.be', 'www.youtu.be'].includes(url.hostname) &&
      url.pathname.length > 1
    );
  } catch {
    return false;
  }
});
const locked = computed(() => props.busy || props.picking);
const canSubmit = computed(
  () =>
    !locked.value &&
    props.toolsAvailable &&
    name.value.trim() &&
    sourceInput.value.trim() &&
    validUrl.value
);
function syncDialog() {
  if (open.value && !dialog.value?.open) dialog.value?.showModal();
  else if (!open.value && dialog.value?.open) dialog.value.close();
}
watch(open, syncDialog, { flush: 'post' });
onMounted(syncDialog);
function close() {
  if (!locked.value) open.value = false;
}
function chooseSource(kind: 'file' | 'url') {
  if (locked.value || sourceKind.value === kind) return;
  sourceKind.value = kind;
  sourceInput.value = '';
}
function sourceKey(event: KeyboardEvent) {
  if (locked.value || !['ArrowRight', 'ArrowLeft'].includes(event.key)) return;
  event.preventDefault();
  chooseSource(sourceKind.value === 'file' ? 'url' : 'file');
  const group = event.currentTarget as HTMLElement;
  void nextTick(() => group.querySelector<HTMLButtonElement>('[aria-checked=true]')?.focus());
}
function submit() {
  if (canSubmit.value)
    emit('submit', {
      name: name.value.trim(),
      sourceInput: sourceInput.value.trim(),
      sourceKind: sourceKind.value,
    });
}
</script>

<template>
  <dialog
    ref="dialog"
    class="modal new-project-dialog"
    aria-labelledby="new-project-title"
    @cancel.prevent="close"
    @close="open = false"
  >
    <form class="new-project-form" @submit.prevent="submit">
      <header>
        <div>
          <h2 id="new-project-title">Novo projeto</h2>
          <p>Escolha a origem do vídeo para começar.</p>
        </div>
        <AppButton
          class="icon-button"
          title="Fechar"
          aria-label="Fechar novo projeto"
          :disabled="locked"
          @click="close"
          ><AppIcon name="close" size="sm"
        /></AppButton>
      </header>
      <div class="source-switch" role="radiogroup" aria-label="Fonte do vídeo" @keydown="sourceKey">
        <button
          type="button"
          role="radio"
          :aria-checked="sourceKind === 'file'"
          :tabindex="sourceKind === 'file' ? 0 : -1"
          :disabled="locked"
          :class="{ selected: sourceKind === 'file' }"
          @click="chooseSource('file')"
        >
          <AppIcon name="video" size="sm" />Arquivo local
        </button>
        <button
          type="button"
          role="radio"
          :aria-checked="sourceKind === 'url'"
          :tabindex="sourceKind === 'url' ? 0 : -1"
          :disabled="locked"
          :class="{ selected: sourceKind === 'url' }"
          @click="chooseSource('url')"
        >
          <AppIcon name="link" size="sm" />Link do YouTube
        </button>
      </div>
      <div v-if="sourceKind === 'file'" class="file-drop">
        <div v-if="sourceInput" class="selected-file-row">
          <div class="file-meta">
            <strong>{{ sourceInput.split(/[\\/]/).pop() }}</strong
            ><small :title="sourceInput">{{ sourceInput }}</small>
          </div>
          <AppButton
            class="button secondary small"
            :disabled="locked"
            @click="$emit('requestFilePicker')"
            >Trocar</AppButton
          >
        </div>
        <div v-else class="file-prompt">
          <AppButton class="button secondary" :disabled="locked" @click="$emit('requestFilePicker')"
            ><AppIcon name="folder-open" size="sm" />Selecionar arquivo de vídeo</AppButton
          ><small>MP4, MOV, MKV ou WebM</small>
        </div>
      </div>
      <label v-else class="field"
        >URL do vídeo
        <input
          v-model="sourceInput"
          type="url"
          placeholder="https://www.youtube.com/watch?v=..."
          :disabled="locked"
          :aria-invalid="!validUrl"
          :aria-describedby="!validUrl ? 'project-url-error' : undefined"
          required
        />
        <small v-if="!validUrl" id="project-url-error" class="form-warning"
          >Informe um link válido do YouTube.</small
        >
      </label>
      <label class="field project-name-field"
        >Nome do projeto
        <input
          v-model="name"
          placeholder="Ex.: Entrevista com especialista"
          maxlength="100"
          :disabled="locked"
          required
        />
      </label>
      <p class="config-summary">{{ configSummary }}</p>
      <div v-if="!setupReady" class="setup-warning">
        <p>
          {{
            !toolsAvailable
              ? 'Localize o FFmpeg e o ffprobe antes de criar o projeto.'
              : 'Configuração incompleta. O projeto será criado sem preparação automática.'
          }}
        </p>
        <AppButton class="button secondary small" :disabled="locked" @click="$emit('openSettings')"
          >Configurar processamento</AppButton
        >
      </div>
      <p v-if="error" role="alert" class="form-warning">{{ error }}</p>
      <footer>
        <AppButton class="button secondary" :disabled="locked" @click="close">Cancelar</AppButton>
        <AppButton type="submit" class="button primary" :disabled="!canSubmit"
          ><AppIcon v-if="busy" name="refresh" size="sm" class="spin" />{{
            busy ? 'Criando projeto…' : setupReady ? 'Criar e preparar' : 'Criar projeto'
          }}</AppButton
        >
      </footer>
    </form>
  </dialog>
</template>

<style scoped>
.new-project-dialog {
  width: min(560px, calc(100vw - 32px));
  max-width: none;
  max-height: calc(100dvh - 32px);
  padding: 0;
  overflow: auto;
  border-radius: var(--radius-panel);
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
}
.new-project-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px;
}
header,
footer,
.selected-file-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
h2 {
  font-size: var(--font-size-title);
  font-weight: 600;
}
header p,
.config-summary,
.file-prompt small {
  font-size: var(--font-size-control);
  color: var(--color-text-secondary);
}
.source-switch {
  display: flex;
  gap: 8px;
  border: 0;
  padding: 0;
}
.source-switch button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex: 1;
  min-height: var(--control-height);
  border: 1px solid transparent;
  border-radius: var(--radius-control);
  color: var(--color-text-secondary);
  font: inherit;
  background: transparent;
}
.source-switch button[aria-checked='true'] {
  background: var(--color-surface-selected);
  border-color: var(--color-border-control);
  color: var(--color-text-primary);
}
.file-drop {
  display: block;
  margin: 0;
  padding: 16px;
  background: var(--color-canvas);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-control);
}
.file-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.file-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 4px;
}
.selected-file-row {
  width: 100%;
  min-width: 0;
}
.selected-file-row :deep(button) {
  flex-shrink: 0;
}
.file-meta strong,
.file-meta small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.file-meta small {
  color: var(--color-text-secondary);
}
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 0;
}
.field input {
  width: 100%;
  min-width: 0;
}
.form-warning {
  color: var(--color-warning-text);
  overflow-wrap: anywhere;
}
.setup-warning {
  display: flex;
  align-items: start;
  gap: 12px;
  font-size: var(--font-size-control);
}
footer {
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid var(--color-border-subtle);
  margin: 0;
}
@media (max-width: 600px) {
  .new-project-form {
    padding: 16px;
  }
  .setup-warning {
    flex-direction: column;
  }
}
</style>
