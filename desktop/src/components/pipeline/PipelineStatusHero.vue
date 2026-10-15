<script setup lang="ts">
import AppButton from '../AppButton.vue';
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
    <p class="preparation-label">Preparação</p>
    <h2 id="pipeline-current-state">{{ status.title }}</h2>
    <p class="hero-description">{{ status.description }}</p>
    <p v-if="status.notice" class="hero-notice">{{ status.notice }}</p>
    <div v-if="status.progress" class="pipeline-progress">
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
  gap: 12px;
  min-width: 0;
  padding: 0 0 24px;
  border-bottom: 1px solid var(--color-border-subtle);
}
.preparation-label {
  color: var(--color-text-secondary);
  font-size: var(--font-size-control);
}
h2 {
  font-size: var(--font-size-title);
  font-weight: 600;
}
.hero-description {
  max-width: 65ch;
  color: var(--color-text-secondary);
}
.hero-notice {
  max-width: 75ch;
  color: var(--color-warning-text);
  overflow-wrap: anywhere;
}
.hero-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 4px;
}
.pipeline-progress {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: min(100%, 560px);
  color: var(--color-text-secondary);
  font-size: var(--font-size-meta);
}
progress {
  width: 100%;
  height: 6px;
  accent-color: var(--color-action-primary);
}
</style>
