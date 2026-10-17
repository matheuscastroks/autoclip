<script setup lang="ts">
import { ref } from 'vue';
import type { PipelineHero, PipelineStep, PipelineAction } from '../../composables/usePipelinePresentation';
import AppButton from '../AppButton.vue';
import AppIcon from '../ui/AppIcon.vue';
import ProcessProgress from '../ui/ProcessProgress.vue';
import TechnicalDiagnosticsDrawer from './TechnicalDiagnosticsDrawer.vue';

const props = defineProps<{
  status: string;
  hero: PipelineHero;
  technicalSteps: PipelineStep[];
  busy?: boolean;
}>();

const emit = defineEmits<{
  action: [value: PipelineAction];
  errorDetails: [];
}>();

const showDiagnostics = ref(false);
</script>

<template>
  <section class="dashboard-card primary-action-card" aria-labelledby="primary-action-heading">
    <header class="card-header">
      <div class="card-header-left">
        <AppIcon name="play" size="sm" class="card-icon" />
        <h3 id="primary-action-heading" class="card-title">Ação do Projeto</h3>
      </div>
      <span class="action-state-chip" :data-state="hero.state">
        <span class="chip-dot" />
        {{ hero.state === 'processing' ? 'Processando' : hero.state === 'ready' ? 'Pronto' : 'Atenção' }}
      </span>
    </header>

    <div class="card-body primary-action-body">
      <!-- Mensagem de Contexto e Próximo Passo -->
      <div class="hero-text-block">
        <strong class="hero-main-title">{{ hero.title }}</strong>
        <p class="hero-main-desc">{{ hero.description }}</p>
        <p v-if="hero.notice" class="hero-notice-desc">{{ hero.notice }}</p>
      </div>

      <!-- Barra de Progresso quando tarefa ativa -->
      <ProcessProgress
        v-if="
          hero.job &&
          hero.job.status !== 'pending' &&
          hero.job.progress &&
          'stage_percent' in hero.job.progress
        "
        :progress="hero.job.progress"
        :status="hero.job.status"
        :started-at="hero.job.started_at"
        :finished-at="hero.job.finished_at"
      />
      <div v-else-if="hero.progress" class="hero-simple-progress">
        <progress
          role="progressbar"
          :aria-label="hero.progress.label"
          :value="hero.progress.value"
          :max="hero.progress.total"
        />
        <span class="progress-label">{{ hero.progress.label }}</span>
      </div>

      <!-- Botões de Ação do Fluxo -->
      <div class="action-buttons-group">
        <AppButton
          v-if="hero.primary"
          class="button primary hero-cta-btn"
          data-action="primary-action"
          :disabled="hero.primary.disabled || busy"
          @click="emit('action', hero.primary)"
        >
          <AppIcon
            :name="hero.primary.id === 'cancel' ? 'warning' : 'sparkle'"
            size="sm"
          />
          {{ hero.primary.label }}
        </AppButton>

        <AppButton
          v-for="secondary in hero.secondary"
          :key="secondary.id"
          class="button secondary"
          :data-action="secondary.id === 'replaceSource' ? 'replace-source' : secondary.id === 'resume' ? 'retry-import' : secondary.id"
          :disabled="secondary.disabled || busy"
          @click="emit('action', secondary)"
        >
          {{ secondary.label }}
        </AppButton>

        <AppButton
          v-if="hero.errorDetails"
          class="button secondary"
          data-action="error-details"
          @click="emit('errorDetails')"
        >
          Ver detalhes técnicos
        </AppButton>
      </div>

      <!-- Rodapé com Link Discreto para Diagnóstico do Motor -->
      <div class="card-footer-diagnostics">
        <button
          type="button"
          class="diagnostics-toggle-link"
          data-action="open-diagnostics"
          @click="showDiagnostics = true"
        >
          <AppIcon name="cpu" size="sm" />
          Ver detalhes técnicos do motor
        </button>
      </div>
    </div>

    <!-- Drawer de Diagnóstico do Motor Local -->
    <TechnicalDiagnosticsDrawer
      :visible="showDiagnostics"
      :steps="technicalSteps"
      @close="showDiagnostics = false"
      @action="emit('action', $event)"
    />
  </section>
</template>

<style scoped>
.primary-action-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.primary-action-card:hover {
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

.action-state-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: var(--radius-control);
  background: var(--color-canvas);
  border: 1px solid var(--color-border-subtle);
  color: var(--color-text-secondary);
}

.action-state-chip[data-state='ready'] {
  border-color: rgba(52, 211, 153, 0.4);
  color: var(--color-success, #34d399);
}

.action-state-chip[data-state='running'] {
  border-color: var(--color-action-primary);
  color: var(--color-action-primary);
}

.chip-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.primary-action-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-text-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.hero-main-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

.hero-main-desc {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.4;
}

.hero-notice-desc {
  margin: 0;
  font-size: 12px;
  color: var(--color-action-primary);
  background: rgba(175, 198, 213, 0.08);
  padding: 6px 10px;
  border-radius: var(--radius-control);
}

.hero-simple-progress {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.hero-simple-progress progress {
  width: 100%;
  height: 8px;
  border-radius: 999px;
  overflow: hidden;
}

.progress-label {
  font-size: 11px;
  color: var(--color-text-secondary);
}

.action-buttons-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-top: 4px;
}

.hero-cta-btn {
  font-size: 13px;
  font-weight: 600;
  padding: 10px 18px;
}

.card-footer-diagnostics {
  margin-top: 4px;
  padding-top: 14px;
  border-top: 1px solid var(--color-border-subtle);
}

.diagnostics-toggle-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-text-muted);
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
  transition: color 0.15s ease;
}

.diagnostics-toggle-link:hover {
  color: var(--color-action-primary);
}
</style>
