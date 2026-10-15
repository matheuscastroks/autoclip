<script setup lang="ts">
import AppButton from './AppButton.vue';
import AppIcon from './ui/AppIcon.vue';
import AppSelect from './AppSelect.vue';
import { computed, ref, nextTick } from 'vue';
import ProjectListItem from './library/ProjectListItem.vue';
import type { Project } from '../types';
import { projectLabel } from '../format';

const props = defineProps<{
  projects: Project[];
  busy: boolean;
  covers?: Record<string, string>;
  activeProjects?: string[];
}>();
defineEmits<{
  open: [id: string];
  create: [];
  import: [];
  delete: [id: string];
  trash: [];
  queue: [];
}>();

const query = ref('');
const filter = ref('all');
const sort = ref('updated');
const viewMode = ref<'grid' | 'list'>('list');
const viewControls = ref<HTMLElement>();
function switchView(mode: 'list' | 'grid') {
  viewMode.value = mode;
  void nextTick(() =>
    viewControls.value?.querySelector<HTMLButtonElement>('[aria-checked=true]')?.focus()
  );
}

const stateOptions = computed(() => [
  { value: 'all', label: 'Todos os estados' },
  ...Array.from(new Set(props.projects.map(p => p.status))).map(state => ({
    value: state,
    label: projectLabel(state),
  })),
]);

const filtered = computed(() =>
  props.projects
    .filter(
      p =>
        (p.title + ' ' + p.name)
          .toLocaleLowerCase('pt-BR')
          .includes(query.value.toLocaleLowerCase('pt-BR')) &&
        (filter.value === 'all' || p.status === filter.value)
    )
    .sort((a, b) =>
      sort.value === 'name'
        ? (a.title || a.name).localeCompare(b.title || b.name, 'pt-BR')
        : b.updated_at - a.updated_at
    )
);
</script>

<template>
  <div class="library-container">
    <!-- Barra de Ferramentas: Busca, Filtros, Ordenação e Alternador de Visão -->
    <section class="library-toolbar">
      <div class="search-box">
        <AppIcon name="search" size="sm" class="search-icon" />
        <input
          type="search"
          v-model="query"
          placeholder="Buscar projetos por título ou nome do arquivo…"
          aria-label="Buscar projetos"
        />
        <button
          v-if="query"
          type="button"
          class="clear-search"
          aria-label="Limpar busca"
          @click="query = ''"
        >
          <AppIcon name="close" size="sm" />
        </button>
      </div>

      <div class="toolbar-controls">
        <label class="control-label">
          <span>Estado:</span>
          <AppSelect v-model="filter" label="Filtrar por estado" :options="stateOptions" />
        </label>

        <label class="control-label">
          <span>Ordenar:</span>
          <AppSelect
            v-model="sort"
            label="Ordenar projetos"
            :options="[
              { value: 'updated', label: 'Mais recentes' },
              { value: 'name', label: 'Nome do projeto' },
            ]"
          />
        </label>

        <div
          ref="viewControls"
          class="view-switcher"
          role="radiogroup"
          aria-label="Modo de visualização"
        >
          <button
            type="button"
            class="view-btn"
            :class="{ active: viewMode === 'grid' }"
            role="radio"
            :aria-checked="viewMode === 'grid'"
            :tabindex="viewMode === 'grid' ? 0 : -1"
            title="Visualização em Grade de Mídia"
            aria-label="Grade de Mídia"
            @click="viewMode = 'grid'"
            @keydown.right.prevent="switchView('list')"
          >
            <AppIcon name="grid" size="sm" />
          </button>
          <button
            type="button"
            class="view-btn"
            :class="{ active: viewMode === 'list' }"
            role="radio"
            :aria-checked="viewMode === 'list'"
            :tabindex="viewMode === 'list' ? 0 : -1"
            title="Visualização em Tabela Estruturada"
            aria-label="Tabela Estruturada"
            @click="viewMode = 'list'"
            @keydown.left.prevent="switchView('grid')"
          >
            <AppIcon name="list" size="sm" />
          </button>
        </div>
        <AppButton
          type="button"
          class="button small secondary"
          data-action="open-project-trash"
          :disabled="busy"
          @click="$emit('trash')"
        >
          <AppIcon name="trash" size="sm" />Lixeira
        </AppButton>
      </div>
    </section>

    <section
      v-if="filtered.length"
      class="project-collection"
      :class="{ 'project-collection--grid': viewMode === 'grid' }"
      :aria-label="viewMode === 'grid' ? 'Projetos em grade' : 'Projetos locais'"
    >
      <ProjectListItem
        v-for="project in filtered"
        :key="project.id"
        :project="project"
        :view="viewMode"
        :thumbnail-url="covers?.[project.id]"
        :busy="busy"
        :is-active="activeProjects?.includes(project.id)"
        @open="$emit('open', project.id)"
        @delete="$emit('delete', project.id)"
      />
    </section>

    <!-- ESTADO 3: ESTADO VAZIO -->
    <section v-if="!filtered.length" class="empty-state studio-empty-state">
      <div class="empty-icon-wrap">
        <AppIcon name="video" size="lg" />
      </div>
      <h2>{{ projects.length ? 'Nenhum resultado encontrado' : 'Nenhum projeto' }}</h2>
      <p>
        {{
          projects.length
            ? 'Tente outros termos de busca ou selecione outro filtro de estado.'
            : 'Importe um vídeo para gerar cortes verticais.'
        }}
      </p>

      <AppButton
        v-if="!projects.length"
        class="button primary start-first-btn"
        :disabled="busy"
        @click="$emit('create')"
      >
        <AppIcon name="add" size="sm" />
        <span>Novo projeto</span>
      </AppButton>
    </section>
  </div>
</template>

<style scoped>
.library-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}
.library-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.search-box {
  position: relative;
  display: flex;
  align-items: center;
  flex: 1 1 240px;
  min-width: 0;
}
.search-icon {
  position: absolute;
  left: 12px;
  color: var(--color-text-muted);
  pointer-events: none;
}
.search-box input {
  width: 100%;
  min-height: var(--control-height);
  padding: 7px 36px;
  background: var(--color-surface);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border-control);
  border-radius: var(--radius-control);
  font: inherit;
}
.clear-search {
  position: absolute;
  right: 8px;
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border: 0;
  background: transparent;
  color: var(--color-text-secondary);
}
.toolbar-controls {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.control-label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-control);
}
.control-label :deep(.el-select) {
  width: 156px;
}
.view-switcher {
  display: flex;
  align-items: center;
  gap: 2px;
}
.view-btn {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border: 1px solid transparent;
  border-radius: var(--radius-control);
  background: transparent;
  color: var(--color-text-secondary);
}
.view-btn:hover {
  background: var(--color-surface-hover);
}
.view-btn.active {
  background: var(--color-surface-selected);
  color: var(--color-text-primary);
}
.project-collection {
  overflow: hidden;
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
}
.project-collection--grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(280px, 100%), 1fr));
  gap: 16px;
  overflow: visible;
  border: 0;
}
.studio-empty-state {
  padding: 48px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
}
.empty-icon-wrap {
  color: var(--color-text-muted);
}
.studio-empty-state h2 {
  font-size: var(--font-size-region);
}
.studio-empty-state p {
  max-width: 44ch;
  color: var(--color-text-secondary);
}
@media (max-width: 1100px) {
  .control-label > span {
    display: none;
  }
}
</style>
