<script setup lang="ts">
import { computed, ref } from 'vue';
import AppIcon from '../ui/AppIcon.vue';
import type { Project } from '../../types';
import { projectLabel, stages, time } from '../../format';

const props = defineProps<{
  project: Project;
  thumbnailUrl?: string;
  busy?: boolean;
  isActive?: boolean;
  view: 'list' | 'grid';
}>();
defineEmits<{ open: []; delete: [] }>();
const brokenUrl = ref('');
const status = computed(() =>
  props.project.status === 'processing' && props.project.summary?.stage
    ? stages[props.project.summary.stage] || projectLabel(props.project.status)
    : projectLabel(props.project.status)
);
const updated = computed(() =>
  props.project.updated_at
    ? new Date(props.project.updated_at * 1000).toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '—'
);
</script>

<template>
  <article
    class="project-list-item"
    :class="{ 'project-list-item--grid': view === 'grid' }"
    :data-project-id="project.id"
    @click="$emit('open')"
  >
    <button
      type="button"
      class="project-open"
      :aria-label="'Abrir projeto: ' + (project.title || project.name)"
      @click.stop="$emit('open')"
    >
      <span class="project-thumbnail">
        <img
          v-if="thumbnailUrl && brokenUrl !== thumbnailUrl"
          :src="thumbnailUrl"
          alt=""
          loading="lazy"
          @error="brokenUrl = thumbnailUrl"
        />
        <AppIcon v-else name="video" size="lg" />
      </span>
      <span class="project-identity">
        <strong :title="project.title || project.name">{{ project.title || project.name }}</strong>
        <span class="project-source">{{
          project.is_manual
            ? 'Teste técnico de renderização'
            : project.has_transcript
              ? `${project.word_count.toLocaleString('pt-BR')} palavras transcritas`
              : project.name
        }}</span>
        <span class="project-duration">{{
          project.duration_us ? time(project.duration_us) : 'Duração pendente'
        }}</span>
      </span>
    </button>
    <span class="project-state" :data-status="project.status">{{ status }}</span>
    <div class="project-summary">
      <span v-if="project.summary?.proposed != null">{{ project.summary.proposed }} propostas</span>
      <span
        v-if="project.summary?.selected != null || project.summary?.generated != null"
        class="project-count-details"
      >
        <template v-if="project.summary?.selected != null"
          >{{ project.summary.selected }} selecionados</template
        >
        <template v-if="project.summary?.selected != null && project.summary?.generated != null">
          ·
        </template>
        <template v-if="project.summary?.generated != null"
          >{{ project.summary.generated }} gerados</template
        >
      </span>
      <span v-if="!project.summary">Resumo indisponível</span>
    </div>
    <time class="project-list-updated" :title="updated">{{ updated }}</time>
    <button
      type="button"
      class="project-delete"
      data-action="delete-project"
      aria-label="Mover projeto para a lixeira"
      title="Mover projeto para a lixeira"
      :disabled="busy || isActive"
      @click.stop="$emit('delete')"
      @keydown.stop
    >
      <AppIcon name="trash" size="sm" />
    </button>
  </article>
</template>

<style scoped>
.project-list-item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 144px 176px 96px 34px;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border-subtle);
  min-width: 0;
  cursor: pointer;
  font-size: var(--font-size-control);
}
.project-list-item:last-child {
  border-bottom: 0;
}
.project-list-item:hover {
  background: var(--color-surface-hover);
}
.project-open {
  display: flex;
  align-items: center;
  gap: 12px;
  text-align: left;
  background: transparent;
  color: var(--color-text-primary);
  border: 0;
  padding: 0;
  min-width: 0;
  width: 100%;
  font: inherit;
}
.project-thumbnail {
  display: grid;
  place-items: center;
  flex: 0 0 64px;
  height: 44px;
  overflow: hidden;
  border-radius: var(--radius-control);
  background: var(--color-canvas);
  color: var(--color-text-muted);
}
.project-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.project-identity {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.project-identity strong {
  font-weight: 600;
  font-size: var(--font-size-body);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.project-source {
  color: var(--color-text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.project-duration,
.project-count-details,
.project-list-updated {
  color: var(--color-text-muted);
  font-size: var(--font-size-meta);
  font-variant-numeric: tabular-nums;
}
.project-state {
  color: var(--color-text-secondary);
  overflow-wrap: anywhere;
}
.project-state[data-status='failed'],
.project-state[data-status='interrupted'] {
  color: var(--color-warning-text);
}
.project-summary {
  display: flex;
  flex-direction: column;
  min-width: 0;
  color: var(--color-text-secondary);
  overflow-wrap: anywhere;
}
.project-delete {
  display: grid;
  place-items: center;
  height: 34px;
  width: 34px;
  padding: 0;
  background: transparent;
  color: var(--color-text-secondary);
  border: 1px solid transparent;
  border-radius: var(--radius-control);
}
.project-delete:hover:not(:disabled) {
  color: var(--color-text-primary);
  background: var(--color-surface-raised);
  border-color: var(--color-border-strong);
}
.project-list-item--grid {
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
}
.project-list-item--grid .project-open {
  grid-column: 1/-1;
  flex-direction: column;
  align-items: stretch;
}
.project-list-item--grid .project-thumbnail {
  flex-basis: auto;
  height: auto;
  aspect-ratio: 16/9;
}
.project-list-item--grid .project-identity strong {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  white-space: normal;
}
.project-list-item--grid .project-state,
.project-list-item--grid .project-summary {
  grid-column: 1/-1;
}
.project-list-item--grid .project-list-updated {
  display: block;
}
@media (max-width: 1100px) {
  .project-list-item:not(.project-list-item--grid) {
    grid-template-columns: minmax(0, 1fr) 132px 156px 34px;
    gap: 12px;
  }
  .project-list-item:not(.project-list-item--grid) .project-list-updated {
    display: none;
  }
}
@media (max-width: 850px) {
  .project-list-item:not(.project-list-item--grid) {
    grid-template-columns: minmax(0, 1fr) 128px 34px;
    gap: 8px;
  }
  .project-list-item:not(.project-list-item--grid) .project-summary {
    grid-column: 1/3;
    padding-left: 76px;
    grid-row: 2;
  }
  .project-list-item:not(.project-list-item--grid) .project-delete {
    grid-column: 3;
    grid-row: 1;
  }
}
</style>
