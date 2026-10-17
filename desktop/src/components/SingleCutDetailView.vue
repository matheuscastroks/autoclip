<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import type { EnrichedCut } from './AllCutsView.vue';
import AppButton from './AppButton.vue';
import AppIcon from './ui/AppIcon.vue';
import StatusTag from './StatusTag.vue';
import { isFinalAvailable, isPreviewAvailable } from '../domain/revisionPresentation';
import { api } from '../api';

const props = defineProps<{
  cut: EnrichedCut;
  busy?: boolean;
}>();

const emit = defineEmits<{
  back: [];
  approve: [cut: EnrichedCut];
  reject: [cut: EnrichedCut];
  renderFinal: [cut: EnrichedCut];
  export: [cut: EnrichedCut];
  openProject: [projectId: string];
}>();

const selectedVersion = ref<'preview' | 'final'>('preview');
const mediaUrl = ref<string>('');
const mediaLoading = ref(false);
const thumbnailUrl = ref<string>('');

const hasFinal = computed(() => isFinalAvailable(props.cut.revision));
const hasPreview = computed(() => isPreviewAvailable(props.cut.revision));

function formatDuration(us: number): string {
  const sec = Math.round(us / 1_000_000);
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

async function loadCutMedia() {
  mediaLoading.value = true;
  try {
    // Carrega a thumbnail com o primeiro frame e título em cima
    try {
      thumbnailUrl.value = await api.media(
        props.cut.project.id,
        'thumbnail-' + props.cut.revision.revision_id
      );
    } catch {
      thumbnailUrl.value = '';
    }

    // Carrega o vídeo conforme a versão selecionada
    if (selectedVersion.value === 'final' && hasFinal.value) {
      mediaUrl.value = await api.media(
        props.cut.project.id,
        props.cut.revision.revision_id
      );
    } else {
      mediaUrl.value = await api.media(
        props.cut.project.id,
        'preview-' + props.cut.revision.revision_id
      );
    }
  } catch (err) {
    console.warn('Falha ao carregar mídia do corte selecionado', err);
  } finally {
    mediaLoading.value = false;
  }
}

watch(
  () => props.cut.revision.revision_id,
  () => {
    selectedVersion.value = hasFinal.value ? 'final' : 'preview';
    void loadCutMedia();
  },
  { immediate: true }
);

watch(selectedVersion, () => {
  void loadCutMedia();
});
</script>

<template>
  <div class="single-cut-detail-view">
    <!-- Barra Superior de Navegação -->
    <header class="detail-nav-bar">
      <button type="button" class="back-link-btn" @click="$emit('back')">
        <AppIcon name="back" size="sm" />
        <span>Voltar para todos os cortes</span>
      </button>

      <div class="nav-bar-actions">
        <button
          type="button"
          class="project-origin-link"
          title="Abrir este projeto no editor"
          @click="$emit('openProject', cut.project.id)"
        >
          <AppIcon name="projects" size="sm" />
          <span>{{ cut.project.title || cut.project.name }}</span>
        </button>

        <StatusTag :status="cut.revision.review_status || 'needs_review'" />
      </div>
    </header>

    <div class="detail-main-layout">
      <!-- Coluna da Esquerda: Player de Vídeo 9:16 -->
      <section class="video-stage-column">
        <div class="video-container-916">
          <video
            v-if="mediaUrl"
            :key="mediaUrl"
            :src="mediaUrl"
            :poster="thumbnailUrl || undefined"
            controls
            playsinline
            preload="metadata"
            class="video-element"
          />
          <div v-else class="video-loading-placeholder">
            <AppIcon name="spinner" size="lg" class="spin" />
            <p>Carregando vídeo do corte…</p>
          </div>
        </div>

        <!-- Seletor de Versão (Prévia / Final) -->
        <div class="version-selector-bar">
          <button
            type="button"
            class="version-btn"
            :class="{ active: selectedVersion === 'preview' }"
            @click="selectedVersion = 'preview'"
          >
            Prévia Rápida (540×960)
          </button>
          <button
            v-if="hasFinal"
            type="button"
            class="version-btn"
            :class="{ active: selectedVersion === 'final' }"
            @click="selectedVersion = 'final'"
          >
            Versão Final (1080×1920)
          </button>
        </div>
      </section>

      <!-- Coluna da Direita: Informações e "O que precisa ser feito" -->
      <section class="info-stage-column">
        <div class="header-info-card">
          <h1 class="cut-heading">{{ cut.revision.title || 'Corte sem título' }}</h1>
          <p v-if="cut.revision.opening_text" class="opening-hook">
            <strong>Gancho de abertura:</strong> "{{ cut.revision.opening_text }}"
          </p>
          <p v-if="cut.revision.rationale" class="cut-rationale">
            {{ cut.revision.rationale }}
          </p>
        </div>

        <!-- Bloco Principal: O Que Precisa Ser Feito Pra Ele -->
        <div class="checklist-panel">
          <h2 class="checklist-heading">
            <AppIcon name="queue" size="sm" />
            O que precisa ser feito pra este corte
          </h2>

          <div class="checklist-steps">
            <!-- Passo 1: Prévia Rápida -->
            <div class="check-step completed">
              <div class="step-indicator">
                <AppIcon name="check" size="sm" />
              </div>
              <div class="step-body">
                <div class="step-title">1. Prévia Rápida & Validação Técnica</div>
                <p class="step-desc">
                  Áudio, corte de silêncio e sincronia de legendas validados localmente.
                </p>
              </div>
            </div>

            <!-- Passo 2: Avaliação Editorial do Editor Humano -->
            <div
              class="check-step"
              :class="{
                completed: cut.revision.review_status === 'approved',
                pending: cut.revision.review_status !== 'approved',
              }"
            >
              <div class="step-indicator">
                <AppIcon
                  :name="cut.revision.review_status === 'approved' ? 'check' : 'eye'"
                  size="sm"
                />
              </div>
              <div class="step-body">
                <div class="step-title">2. Aprovação Editorial</div>
                <p class="step-desc">
                  {{
                    cut.revision.review_status === 'approved'
                      ? 'Corte aprovado para geração da versão final em alta resolução.'
                      : 'Avalie se a narrativa funciona fora do contexto original e se o corte está pronto.'
                  }}
                </p>

                <div v-if="cut.revision.review_status !== 'approved'" class="step-action-row">
                  <AppButton
                    class="button small primary"
                    :disabled="busy"
                    @click="$emit('approve', cut)"
                  >
                    <AppIcon name="check" size="sm" />
                    Aprovar Corte
                  </AppButton>
                  <AppButton
                    class="button small secondary"
                    :disabled="busy"
                    @click="$emit('reject', cut)"
                  >
                    Rejeitar
                  </AppButton>
                </div>
              </div>
            </div>

            <!-- Passo 3: Versão Final 1080x1920 -->
            <div
              class="check-step"
              :class="{
                completed: hasFinal,
                pending: !hasFinal && cut.revision.review_status === 'approved',
                locked: !hasFinal && cut.revision.review_status !== 'approved',
              }"
            >
              <div class="step-indicator">
                <AppIcon
                  :name="hasFinal ? 'check' : 'sparkle'"
                  size="sm"
                />
              </div>
              <div class="step-body">
                <div class="step-title">3. Versão Final em Alta Resolução (1080×1920)</div>
                <p class="step-desc">
                  {{
                    hasFinal
                      ? 'Vídeo renderizado com enquadramento inteligente e nitidez máxima.'
                      : cut.revision.review_status === 'approved'
                        ? 'Corte aprovado! Pronto para renderizar o vídeo final.'
                        : 'Aguardando aprovação editorial para habilitar renderização final.'
                  }}
                </p>

                <div
                  v-if="!hasFinal && cut.revision.review_status === 'approved'"
                  class="step-action-row"
                >
                  <AppButton
                    class="button small primary"
                    :disabled="busy"
                    @click="$emit('renderFinal', cut)"
                  >
                    <AppIcon name="sparkle" size="sm" />
                    Gerar Versão Final 1080×1920
                  </AppButton>
                </div>
              </div>
            </div>

            <!-- Passo 4: Exportação -->
            <div
              class="check-step"
              :class="{
                completed: cut.revision.exported,
                pending: !cut.revision.exported && hasFinal && cut.revision.review_status === 'approved',
                locked: !hasFinal || cut.revision.review_status !== 'approved',
              }"
            >
              <div class="step-indicator">
                <AppIcon
                  :name="cut.revision.exported ? 'check' : 'download'"
                  size="sm"
                />
              </div>
              <div class="step-body">
                <div class="step-title">4. Exportar Vídeo Final</div>
                <p class="step-desc">
                  {{
                    cut.revision.exported
                      ? 'Vídeo exportado e disponível na Central de Exportações e na pasta do projeto.'
                      : hasFinal
                        ? 'Vídeo pronto para exportação para YouTube Shorts, Reels e TikTok.'
                        : 'Requer versão final gerada.'
                  }}
                </p>

                <div
                  v-if="!cut.revision.exported && hasFinal && cut.revision.review_status === 'approved'"
                  class="step-action-row"
                >
                  <AppButton
                    class="button small primary"
                    :disabled="busy"
                    @click="$emit('export', cut)"
                  >
                    <AppIcon name="download" size="sm" />
                    Exportar Corte
                  </AppButton>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Metadados Técnicos Rápidos -->
        <div class="specs-grid">
          <div class="spec-card">
            <span class="spec-label">Duração</span>
            <span class="spec-value">{{ formatDuration(cut.revision.duration_us ?? 0) }}</span>
          </div>
          <div class="spec-card">
            <span class="spec-label">Formato</span>
            <span class="spec-value">9:16 Vertical</span>
          </div>
          <div class="spec-card">
            <span class="spec-label">Status Final</span>
            <span class="spec-value">{{ hasFinal ? 'Renderizado' : 'Pendente' }}</span>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.single-cut-detail-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.detail-nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 18px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
}

.back-link-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  border: none;
  color: var(--color-action-primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.15s ease;
}

.back-link-btn:hover {
  background: var(--color-surface-hover);
}

.nav-bar-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.project-origin-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
  border-radius: 4px;
  padding: 4px 10px;
  font-size: 12px;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: color 0.15s ease, border-color 0.15s ease;
}

.project-origin-link:hover {
  color: var(--color-text-primary);
  border-color: var(--color-border-strong);
}

.detail-main-layout {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 28px;
  align-items: start;
}

@media (max-width: 900px) {
  .detail-main-layout {
    grid-template-columns: 1fr;
  }
}

/* Coluna de Vídeo */
.video-stage-column {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.video-container-916 {
  width: 100%;
  aspect-ratio: 9 / 16;
  max-height: 560px;
  background: #000;
  border-radius: var(--radius-panel);
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  border: 1px solid var(--color-border-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-element {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #000;
}

.video-loading-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  color: var(--color-text-muted);
  font-size: 13px;
}

.version-selector-bar {
  display: flex;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: 6px;
  padding: 3px;
}

.version-btn {
  flex: 1;
  padding: 6px 10px;
  font-size: 12px;
  font-weight: 500;
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.version-btn.active {
  background: var(--color-surface-raised);
  color: var(--color-text-primary);
  font-weight: 600;
}

/* Coluna de Informações e Checklist */
.info-stage-column {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.header-info-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cut-heading {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.3;
}

.opening-hook {
  margin: 0;
  font-size: 14px;
  color: var(--color-action-primary);
  background: rgba(175, 198, 213, 0.08);
  padding: 8px 12px;
  border-radius: 6px;
  border-left: 3px solid var(--color-action-primary);
}

.cut-rationale {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* Checklist: O que precisa ser feito */
.checklist-panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.checklist-heading {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.checklist-steps {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.check-step {
  display: flex;
  gap: 14px;
  padding: 12px 14px;
  border-radius: 8px;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
}

.check-step.completed {
  border-color: rgba(52, 211, 153, 0.25);
  background: rgba(52, 211, 153, 0.04);
}

.check-step.pending {
  border-color: rgba(175, 198, 213, 0.35);
  background: rgba(175, 198, 213, 0.05);
}

.check-step.locked {
  opacity: 0.6;
}

.step-indicator {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: none;
  background: var(--color-surface);
  color: var(--color-text-muted);
}

.check-step.completed .step-indicator {
  background: var(--color-success);
  color: #000;
}

.check-step.pending .step-indicator {
  background: var(--color-action-primary);
  color: #000;
}

.step-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.step-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.step-desc {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.4;
}

.step-action-row {
  display: flex;
  gap: 8px;
  margin-top: 6px;
}

/* Specs */
.specs-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.spec-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: 8px;
}

.spec-label {
  font-size: 11px;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.spec-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}
</style>
