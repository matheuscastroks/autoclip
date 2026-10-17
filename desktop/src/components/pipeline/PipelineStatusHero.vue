<script setup lang="ts">
import AppButton from '../AppButton.vue';
import ProcessProgress from '../ui/ProcessProgress.vue';
import type { PipelineHero, PipelineAction } from '../../composables/usePipelinePresentation';
defineProps<{ status: PipelineHero }>();
defineEmits<{ action: [value: PipelineAction]; errorDetails: [] }>();
</script>

<template>
  <section
    class="state-hero-card"
    :data-state="status.state"
    aria-labelledby="pipeline-current-state"
  >
    <div class="hero-eyebrow">
      <span class="eyebrow-pill">Preparação do Projeto</span>
      <span v-if="status.state" class="state-chip" :data-state="status.state">
        <span class="chip-dot" />
        {{ status.state }}
      </span>
    </div>

    <h2 id="pipeline-current-state" class="hero-title">{{ status.title }}</h2>
    <p class="hero-description">{{ status.description }}</p>
    <p v-if="status.notice" class="hero-notice">{{ status.notice }}</p>

    <ProcessProgress
      v-if="
        status.job &&
        status.job.status !== 'pending' &&
        status.job.progress &&
        'stage_percent' in status.job.progress
      "
      :progress="status.job.progress"
      :status="status.job.status"
      :started-at="status.job.started_at"
      :finished-at="status.job.finished_at"
    />
    <div v-else-if="status.progress" class="pipeline-progress">
      <progress
        role="progressbar"
        :aria-label="status.progress.label"
        :value="status.progress.value"
        :max="status.progress.total"
      />
      <span>{{ status.progress.label }}</span>
    </div>

    <div class="hero-actions">
      <AppButton
        v-if="status.primary"
        class="button hero-primary-btn"
        :class="status.primary.id === 'cancel' ? 'secondary' : 'primary'"
        :data-action="status.primary.id === 'resume' ? 'retry-import' : status.primary.id"
        :disabled="status.primary.disabled"
        @click="$emit('action', status.primary)"
        >{{ status.primary.label }}</AppButton
      >
      <AppButton
        v-for="action in status.secondary"
        :key="action.id"
        class="button secondary"
        :data-action="action.id === 'replaceSource' ? 'replace-source' : action.id"
        :disabled="action.disabled"
        @click="$emit('action', action)"
        >{{ action.label }}</AppButton
      >
      <AppButton
        v-if="status.errorDetails"
        class="button secondary"
        data-action="error-details"
        @click="$emit('errorDetails')"
        >Ver detalhes técnicos</AppButton
      >
    </div>
  </section>
</template>

<style scoped>
.state-hero-card {
  display: flex;
  flex-direction: column;
  align-items: start;
  gap: 14px;
  min-width: 0;
  padding: 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.state-hero-card:hover {
  border-color: var(--color-border-strong);
}

.hero-eyebrow {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.eyebrow-pill {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary);
}

.state-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 8px;
  font-size: 11px;
  font-weight: 500;
  border-radius: 999px;
  background: var(--color-surface-raised);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-subtle);
  text-transform: capitalize;
}

.chip-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background-color: var(--color-action-primary);
}

.hero-title {
  font-size: var(--font-size-title);
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
  margin: 0;
  line-height: 1.25;
}

.hero-description {
  max-width: 68ch;
  color: var(--color-text-secondary);
  font-size: var(--font-size-body);
  line-height: 1.5;
  margin: 0;
}

.hero-notice {
  max-width: 75ch;
  color: var(--color-warning-text);
  background: var(--color-warning-surface);
  border: 1px solid var(--color-warning-border);
  padding: 8px 12px;
  border-radius: var(--radius-control);
  font-size: var(--font-size-control);
  overflow-wrap: anywhere;
  margin: 0;
}

.hero-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 6px;
}

.pipeline-progress {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  max-width: 560px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-meta);
}

progress {
  width: 100%;
  height: 6px;
  border-radius: 999px;
  overflow: hidden;
  accent-color: var(--color-action-primary);
}
</style>
