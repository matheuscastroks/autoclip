<script setup lang="ts">
import { computed } from 'vue';
import type { AnalysisView } from '../../types';
import AppIcon from '../ui/AppIcon.vue';
import AppButton from '../AppButton.vue';

const props = defineProps<{
  hasTranscript: boolean;
  analysis?: AnalysisView | null;
  wordCount?: number;
}>();

const emit = defineEmits<{
  openTranscript: [];
  openAnalysis: [];
}>();

const topicsList = computed<string[]>(() => {
  if (!props.analysis) return [];
  const fromTopics = props.analysis.topics?.map(t => t.title).filter(Boolean) || [];
  if (fromTopics.length) return fromTopics;
  const titles = props.analysis.proposals?.map(p => p.topic_title).filter(Boolean) || [];
  return Array.from(new Set(titles));
});

const proposalsCount = computed(() => props.analysis?.proposals?.length || 0);
</script>

<template>
  <section class="dashboard-card content-xray-card" aria-labelledby="content-xray-heading">
    <header class="card-header">
      <div class="card-header-left">
        <AppIcon name="sparkle" size="sm" class="card-icon" />
        <h3 id="content-xray-heading" class="card-title">Raio-X do Conteúdo</h3>
      </div>
      <span v-if="topicsList.length" class="xray-badge">
        {{ topicsList.length }} temas detectados
      </span>
    </header>

    <div class="card-body content-xray-body">
      <!-- Caso 1: Quando a análise já foi realizada e temos tópicos -->
      <div v-if="topicsList.length" class="xray-content-ready">
        <div class="xray-summary-row">
          <div class="summary-stat">
            <span class="stat-number">{{ proposalsCount }}</span>
            <span class="stat-label"> propostas de cortes</span>
          </div>
          <div class="summary-stat">
            <span class="stat-number">{{ topicsList.length }}</span>
            <span class="stat-label"> assuntos principais</span>
          </div>
        </div>

        <div class="topics-tag-cloud">
          <span v-for="topic in topicsList" :key="topic" class="topic-tag">
            <AppIcon name="tag" size="sm" class="topic-icon" />
            {{ topic }}
          </span>
        </div>

        <div class="xray-actions-row">
          <AppButton
            class="button secondary small"
            data-action="open-transcript"
            @click="emit('openTranscript')"
          >
            <AppIcon name="transcript" size="sm" />
            Ver Transcrição Completa
          </AppButton>
          <AppButton
            v-if="proposalsCount > 0"
            class="button secondary small"
            data-action="open-analysis"
            @click="emit('openAnalysis')"
          >
            <AppIcon name="search" size="sm" />
            Explorar Propostas
          </AppButton>
        </div>
      </div>

      <!-- Caso 2: Quando já transcreveu mas ainda não analisou -->
      <div v-else-if="hasTranscript" class="xray-transcribed-notice">
        <div class="notice-icon-box">
          <AppIcon name="transcript" size="md" />
        </div>
        <div class="notice-copy">
          <strong>Transcrição pronta</strong>
          <p>
            O áudio foi transcrito com sucesso. Inicie a análise por IA para identificar os temas
            principais e selecionar os melhores ganchos virais.
          </p>
        </div>
        <AppButton
          class="button secondary small"
          data-action="open-transcript"
          @click="emit('openTranscript')"
        >
          <AppIcon name="transcript" size="sm" />
          Conferir Transcrição
        </AppButton>
      </div>

      <!-- Caso 3: Estado inicial, aguardando transcrição -->
      <div v-else class="xray-pending-notice">
        <div class="notice-icon-box subtle">
          <AppIcon name="clock" size="md" />
        </div>
        <div class="notice-copy">
          <strong>Raio-X Pendente</strong>
          <p>
            Após a transcrição do áudio, a inteligência artificial analisará o ritmo, temas e
            destaques do vídeo para sugerir cortes virais.
          </p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.content-xray-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: border-color 0.2s ease;
}

.content-xray-card:hover {
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

.xray-badge {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-action-primary);
  background: rgba(175, 198, 213, 0.12);
  padding: 2px 8px;
  border-radius: var(--radius-control);
}

.content-xray-body {
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.xray-content-ready {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.xray-summary-row {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 12px 14px;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-control);
}

.summary-stat {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.stat-number {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-action-primary);
  font-feature-settings: 'tnum';
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.topics-tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.topic-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-primary);
  background: var(--color-canvas);
  border: 1px solid var(--color-border-subtle);
  padding: 5px 10px;
  border-radius: var(--radius-control);
  transition: all 0.15s ease;
}

.topic-tag:hover {
  border-color: var(--color-action-primary);
  background: var(--color-surface-raised);
}

.topic-icon {
  color: var(--color-action-primary);
}

.xray-actions-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 4px;
}

.xray-transcribed-notice,
.xray-pending-notice {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 14px 16px;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-control);
}

.notice-icon-box {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: rgba(175, 198, 213, 0.15);
  color: var(--color-action-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.notice-icon-box.subtle {
  background: var(--color-canvas);
  color: var(--color-text-muted);
}

.notice-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.notice-copy strong {
  font-size: 13px;
  color: var(--color-text-primary);
}

.notice-copy p {
  margin: 0;
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.4;
}
</style>
