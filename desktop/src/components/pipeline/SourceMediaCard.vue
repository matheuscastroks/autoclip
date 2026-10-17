<script setup lang="ts">
import { computed, ref } from 'vue';
import { time } from '../../format';
import { vRecoverMedia } from '../../directives/recoverMedia';
import AppIcon from '../ui/AppIcon.vue';

const props = defineProps<{
  sourceUrl?: string;
  durationUs?: number;
  wordCount?: number;
  title?: string;
  sourceType?: string;
}>();

const player = ref<HTMLVideoElement>();
const mediaError = ref('');

const formattedDuration = computed(() => {
  if (!props.durationUs) return '—';
  return time(props.durationUs);
});

const formattedWords = computed(() => {
  if (typeof props.wordCount !== 'number' || props.wordCount <= 0) return 'Aguardando transcrição';
  return `${props.wordCount.toLocaleString('pt-BR')} palavras`;
});
</script>

<template>
  <section class="dashboard-card source-media-card" aria-labelledby="source-media-heading">
    <header class="card-header">
      <div class="card-header-left">
        <AppIcon name="video" size="sm" class="card-icon" />
        <h3 id="source-media-heading" class="card-title">Vídeo Original</h3>
      </div>
      <span v-if="title" class="media-title-chip" :title="title">{{ title }}</span>
    </header>

    <div class="card-body source-media-body">
      <!-- Player de Vídeo Original -->
      <div v-if="sourceUrl" class="player-container">
        <video
          ref="player"
          v-recover-media="sourceUrl"
          :src="sourceUrl"
          controls
          preload="metadata"
          playsinline
          aria-label="Reprodução do vídeo original"
          @loadedmetadata="mediaError = ''"
        />
        <p v-if="mediaError" class="media-error-notice" role="alert">{{ mediaError }}</p>
      </div>

      <!-- Placeholder quando vídeo não disponível -->
      <div v-else class="media-placeholder">
        <AppIcon name="warning" size="md" />
        <p class="placeholder-text">Vídeo original não disponível para reprodução imediata.</p>
      </div>

      <!-- Grade de Metadados Claros e Humanos -->
      <div class="media-specs-grid">
        <div class="spec-chip">
          <span class="spec-label">
            <AppIcon name="clock" size="sm" />
            Duração
          </span>
          <strong class="spec-value">{{ formattedDuration }}</strong>
        </div>

        <div class="spec-chip">
          <span class="spec-label">
            <AppIcon name="transcript" size="sm" />
            Volume de Fala
          </span>
          <strong class="spec-value">{{ formattedWords }}</strong>
        </div>

        <div class="spec-chip">
          <span class="spec-label">
            <AppIcon name="globe" size="sm" />
            Idioma Detectado
          </span>
          <strong class="spec-value">Português (BR)</strong>
        </div>

        <div class="spec-chip">
          <span class="spec-label">
            <AppIcon name="sparkle" size="sm" />
            Formato Original
          </span>
          <strong class="spec-value">Horizontal (16:9)</strong>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.source-media-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: border-color 0.2s ease;
}

.source-media-card:hover {
  border-color: var(--color-border-strong);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border-subtle);
  background: var(--color-surface-raised);
}

.card-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

.media-title-chip {
  font-size: 11px;
  color: var(--color-text-secondary);
  background: var(--color-canvas);
  border: 1px solid var(--color-border-subtle);
  padding: 3px 8px;
  border-radius: var(--radius-control);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-media-body {
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.player-container {
  width: 100%;
  aspect-ratio: 16/9;
  background: #000;
  border-radius: var(--radius-control);
  overflow: hidden;
  border: 1px solid var(--color-border-subtle);
}

.player-container video {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: contain;
}

.media-placeholder {
  width: 100%;
  aspect-ratio: 16/9;
  background: var(--color-canvas);
  border: 1px dashed var(--color-border-strong);
  border-radius: var(--radius-control);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--color-text-muted);
  padding: 20px;
  text-align: center;
}

.placeholder-text {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.media-specs-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.spec-chip {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-control);
}

.spec-label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.spec-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  font-feature-settings: 'tnum';
}

@media (max-width: 600px) {
  .media-specs-grid {
    grid-template-columns: 1fr;
  }
}
</style>
