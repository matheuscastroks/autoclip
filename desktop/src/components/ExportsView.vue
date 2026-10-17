<script setup lang="ts">
import { computed, ref } from 'vue';
import type { Project, Revision } from '../types';
import AppButton from './AppButton.vue';
import AppIcon from './ui/AppIcon.vue';

export interface ExportedCutItem {
  revision: Revision;
  project: Project;
}

const props = defineProps<{
  exportedCuts: ExportedCutItem[];
  loading?: boolean;
}>();

const emit = defineEmits<{
  openFolder: [projectId: string];
  play: [cut: ExportedCutItem];
  openProject: [projectId: string];
}>();

const copiedId = ref<string | null>(null);

function formatDuration(us: number): string {
  const sec = Math.round(us / 1_000_000);
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function generateCopyText(item: ExportedCutItem): string {
  if (item.revision.description && item.revision.description.trim()) {
    return item.revision.description.trim();
  }
  const title = item.revision.title || item.project.title || 'Corte em Destaque';
  return `${title}\n\nAssista ao episódio completo no canal!\n\n#shorts #cortes #podcast #reels`;
}

async function copyPostCopy(item: ExportedCutItem) {
  const text = generateCopyText(item);
  try {
    await navigator.clipboard.writeText(text);
    copiedId.value = item.revision.revision_id;
    setTimeout(() => {
      if (copiedId.value === item.revision.revision_id) copiedId.value = null;
    }, 2500);
  } catch (err) {
    console.error('Falha ao copiar texto para área de transferência', err);
  }
}
</script>

<template>
  <div class="exports-view">
    <header class="exports-header">
      <div class="header-titles">
        <h1 class="view-title">Central de Exportações</h1>
        <p class="view-subtitle">
          Seus vídeos finais renderizados em 9:16 prontos para publicação, com copy e hashtags geradas pela IA.
        </p>
      </div>

      <div class="header-count-badge">
        <span class="count-number">{{ exportedCuts.length }}</span>
        <span class="count-label">Vídeos Exportados</span>
      </div>
    </header>

    <!-- Lista de Exportações Prontas -->
    <div v-if="exportedCuts.length" class="exports-grid">
      <article
        v-for="item in exportedCuts"
        :key="item.revision.revision_id"
        class="export-card"
      >
        <!-- Coluna Visual / Miniatura 9:16 -->
        <div class="export-thumb-col">
          <div class="thumb-916" @click="$emit('play', item)">
            <div class="thumb-ambient">
              <AppIcon name="video" size="lg" />
            </div>
            <div class="play-overlay-btn" title="Reproduzir vídeo exportado">
              <AppIcon name="play" size="md" />
            </div>
            <span class="duration-tag">{{ formatDuration(item.revision.duration_us ?? 0) }}</span>
          </div>
        </div>

        <!-- Coluna de Conteúdo e Metadados para Publicação -->
        <div class="export-details-col">
          <div class="details-top">
            <div class="details-meta-row">
              <button
                type="button"
                class="project-badge-link"
                title="Abrir este projeto"
                @click="$emit('openProject', item.project.id)"
              >
                <AppIcon name="projects" size="sm" />
                <span>{{ item.project.title || item.project.name }}</span>
              </button>

              <span class="format-spec-tag">1080×1920 (9:16) · MP4</span>
            </div>

            <h3 class="export-title">{{ item.revision.title || 'Corte sem título' }}</h3>
          </div>

          <!-- Caixa de Copy da IA para Publicação -->
          <div class="social-copy-box">
            <div class="copy-box-header">
              <span class="copy-label">
                <AppIcon name="sparkle" size="sm" />
                Texto sugerido para redes sociais
              </span>
              <button
                type="button"
                class="copy-quick-action"
                :class="{ copied: copiedId === item.revision.revision_id }"
                @click="copyPostCopy(item)"
              >
                <AppIcon :name="copiedId === item.revision.revision_id ? 'check' : 'transcript'" size="sm" />
                {{ copiedId === item.revision.revision_id ? 'Copiado!' : 'Copiar texto' }}
              </button>
            </div>
            <p class="copy-content-preview">{{ generateCopyText(item) }}</p>
          </div>

          <!-- Ações do Arquivo -->
          <div class="details-bottom-actions">
            <AppButton
              class="button secondary small"
              @click="$emit('openFolder', item.project.id)"
            >
              <AppIcon name="folder-open" size="sm" />
              Abrir pasta no computador
            </AppButton>

            <AppButton
              class="button primary small"
              :class="{ 'button--success': copiedId === item.revision.revision_id }"
              @click="copyPostCopy(item)"
            >
              <AppIcon :name="copiedId === item.revision.revision_id ? 'check' : 'transcript'" size="sm" />
              {{ copiedId === item.revision.revision_id ? 'Texto Copiado!' : 'Copiar para Publicação' }}
            </AppButton>
          </div>
        </div>
      </article>
    </div>

    <!-- Estado Vazio -->
    <div v-else class="exports-empty-state">
      <div class="empty-icon-wrap">
        <AppIcon name="download" size="lg" />
      </div>
      <h3>Nenhum corte exportado ainda</h3>
      <p>
        Acesse a aba <strong>Todos os Cortes</strong> ou a biblioteca de projetos, aprove os cortes desejados e clique em <strong>Exportar</strong>. Seus arquivos finais e legendas aparecerão prontos aqui.
      </p>
    </div>
  </div>
</template>

<style scoped>
.exports-view {
  display: flex;
  flex-direction: column;
  gap: 28px;
  padding: 32px;
  max-width: 1300px;
  margin: 0 auto;
  width: 100%;
}

.exports-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}

.header-titles {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.view-title {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--color-text-primary);
  margin: 0;
}

.view-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
  max-width: 650px;
}

.header-count-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 18px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-control);
}

.count-number {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-success);
  line-height: 1.2;
}

.count-label {
  font-size: 11px;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Exports Grid */
.exports-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.export-card {
  display: flex;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
  overflow: hidden;
  transition: all 0.2s cubic-bezier(0.32, 0.72, 0, 1);
}

.export-card:hover {
  border-color: var(--color-border-strong);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

/* Thumbnail Column */
.export-thumb-col {
  width: 140px;
  flex-shrink: 0;
  background: var(--color-canvas);
  border-right: 1px solid var(--color-border-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
}

.thumb-916 {
  position: relative;
  width: 100%;
  aspect-ratio: 9 / 16;
  max-height: 240px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  overflow: hidden;
}

.thumb-ambient {
  color: var(--color-text-muted);
  opacity: 0.5;
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.thumb-916:hover .thumb-ambient {
  opacity: 0.8;
  transform: scale(1.08);
}

.play-overlay-btn {
  position: absolute;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(16, 19, 22, 0.75);
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  transition: all 0.15s ease;
}

.thumb-916:hover .play-overlay-btn {
  background: var(--color-action-primary);
  color: var(--color-action-primary-text);
  transform: scale(1.08);
}

.duration-tag {
  position: absolute;
  bottom: 8px;
  right: 8px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  font-family: ui-monospace, monospace;
}

/* Details Column */
.export-details-col {
  display: flex;
  flex-direction: column;
  padding: 20px 24px;
  gap: 16px;
  flex: 1;
  min-width: 0;
}

.details-top {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.details-meta-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.project-badge-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
  border-radius: 4px;
  color: var(--color-text-secondary);
  font-size: 11px;
  font-weight: 500;
  padding: 3px 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.project-badge-link:hover {
  border-color: var(--color-border-strong);
  color: var(--color-text-primary);
}

.format-spec-tag {
  font-size: 11px;
  color: var(--color-text-muted);
  font-family: ui-monospace, monospace;
}

.export-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
  line-height: 1.35;
}

/* Social Copy Box */
.social-copy-box {
  background: var(--color-canvas);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-control);
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.copy-box-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.copy-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-action-primary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.copy-quick-action {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.copy-quick-action:hover {
  color: var(--color-text-primary);
}

.copy-quick-action.copied {
  color: var(--color-success);
  font-weight: 600;
}

.copy-content-preview {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  white-space: pre-line;
  max-height: 72px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Bottom Actions */
.details-bottom-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  margin-top: auto;
  padding-top: 6px;
}

.button--success {
  background: var(--color-success) !important;
  color: #000 !important;
  border-color: var(--color-success) !important;
}

/* Empty State */
.exports-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 60px 20px;
  background: var(--color-surface);
  border: 1px dashed var(--color-border-subtle);
  border-radius: var(--radius-panel);
}

.empty-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-action-primary);
  margin-bottom: 16px;
}

.exports-empty-state h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 8px;
}

.exports-empty-state p {
  font-size: 13px;
  color: var(--color-text-secondary);
  max-width: 440px;
  margin: 0;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .export-card {
    flex-direction: column;
  }
  .export-thumb-col {
    width: 100%;
    aspect-ratio: 16 / 9;
  }
}
</style>
