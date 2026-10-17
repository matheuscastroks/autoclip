<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import type { PipelineStep, PipelineAction } from '../../composables/usePipelinePresentation';
import PipelineStepList from './PipelineStepList.vue';
import AppIcon from '../ui/AppIcon.vue';

const props = defineProps<{
  visible: boolean;
  steps: PipelineStep[];
}>();

const emit = defineEmits<{
  close: [];
  action: [value: PipelineAction];
}>();

function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.visible) {
    emit('close');
  }
}

onMounted(() => window.addEventListener('keydown', onKeyDown));
onUnmounted(() => window.removeEventListener('keydown', onKeyDown));
</script>

<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="diagnostics-drawer-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="diagnostics-drawer-title"
      @click.self="emit('close')"
    >
      <div class="diagnostics-drawer-panel">
        <header class="drawer-header">
          <div class="drawer-header-left">
            <AppIcon name="cpu" size="sm" class="drawer-icon" />
            <h3 id="diagnostics-drawer-title" class="drawer-title">Diagnóstico do Motor Local</h3>
          </div>
          <button
            type="button"
            class="drawer-close-btn"
            aria-label="Fechar diagnóstico"
            @click="emit('close')"
          >
            <AppIcon name="close" size="sm" />
          </button>
        </header>

        <div class="drawer-body">
          <p class="drawer-intro">
            Fases técnicas internas executadas pelo motor local (FFmpeg, Whisper ASR, Silero VAD e
            pipeline de renderização).
          </p>
          <PipelineStepList :steps="steps" technical @action="emit('action', $event)" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.diagnostics-drawer-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(3px);
  display: flex;
  justify-content: flex-end;
}

.diagnostics-drawer-panel {
  width: 100%;
  max-width: 480px;
  height: 100%;
  background: var(--color-surface);
  border-left: 1px solid var(--color-border-subtle);
  display: flex;
  flex-direction: column;
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.4);
  animation: slideIn 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border-subtle);
  background: var(--color-surface-raised);
}

.drawer-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.drawer-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.drawer-icon {
  color: var(--color-action-primary);
}

.drawer-close-btn {
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.drawer-close-btn:hover {
  background: var(--color-surface-hover);
  color: var(--color-text-primary);
}

.drawer-body {
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 1;
}

.drawer-intro {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}
</style>
