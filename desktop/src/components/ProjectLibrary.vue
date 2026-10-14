<script setup lang="ts">
import AppButton from './AppButton.vue';
import AppSelect from './AppSelect.vue';
import { computed, ref } from 'vue';
import { ElTag, ElTooltip } from 'element-plus';
import {
  Search,
  Film,
  Trash2,
  Plus,
  FileVideo,
  ListOrdered,
  LayoutGrid,
  List,
  Clock,
  Sparkles,
} from '@lucide/vue';
import type { Project } from '../types';
import { time, labels, stages } from '../format';

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
const brokenCovers = ref<Record<string, string>>({});

const stateOptions = computed(() => [
  { value: 'all', label: 'Todos os estados' },
  ...Array.from(new Set(props.projects.map(p => p.status))).map(state => ({
    value: state,
    label: labels[state] || state,
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

function updated(value: number) {
  return value
    ? new Date(value * 1000).toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '—';
}

function timeAgo(value: number) {
  if (!value) return 'Recente';
  const diffSec = Math.floor(Date.now() / 1000 - value);
  if (diffSec < 60) return 'Agora mesmo';
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)} min atrás`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} h atrás`;
  return `${Math.floor(diffSec / 86400)} d atrás`;
}
</script>

<template>
  <div class="library-container">
    <!-- Barra de Ferramentas: Busca, Filtros, Ordenação e Alternador de Visão -->
    <section class="library-toolbar">
      <div class="search-box">
        <Search :size="16" class="search-icon" />
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
          ✕
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

        <div class="view-switcher" role="radiogroup" aria-label="Modo de visualização">
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
            @keydown.right.prevent="viewMode = 'list'"
          >
            <LayoutGrid :size="16" />
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
            @keydown.left.prevent="viewMode = 'grid'"
          >
            <List :size="16" />
          </button>
        </div>
      </div>
    </section>

    <!-- ESTADO 1: GRADE VISUAL DE MÍDIA (Modo Padrão de Estúdio) -->
    <section
      v-if="filtered.length && viewMode === 'grid'"
      class="projects-media-grid"
      aria-label="Projetos em grade"
    >
      <article
        v-for="project in filtered"
        :key="project.id"
        class="media-project-card"
        :data-project-id="project.id"
        tabindex="0"
        role="button"
        :aria-label="'Abrir projeto: ' + (project.title || project.name)"
        @click="$emit('open', project.id)"
        @keydown.enter.prevent="$emit('open', project.id)"
        @keydown.space.prevent="$emit('open', project.id)"
      >
        <!-- Thumbnail 16:9 com Badges Flutuantes -->
        <div class="card-thumbnail-wrap">
          <img
            v-if="covers?.[project.id] && brokenCovers[project.id] !== covers[project.id]"
            :src="covers[project.id]"
            alt=""
            loading="lazy"
            class="thumbnail-img"
            @error="brokenCovers[project.id] = covers?.[project.id] || ''"
          />
          <div v-else class="thumbnail-fallback">
            <Film :size="32" />
          </div>

          <!-- Duração do vídeo -->
          <span class="video-duration-tag">
            <Clock :size="11" />
            {{ project.duration_us ? time(project.duration_us) : '—' }}
          </span>

          <!-- Status do projeto -->
          <el-tag
            :type="
              project.status === 'ready' || project.status === 'completed'
                ? 'success'
                : project.status === 'processing' || project.status === 'running'
                  ? 'warning'
                  : project.status === 'failed'
                    ? 'danger'
                    : 'info'
            "
            effect="dark"
            size="small"
            class="status-pill card-status-pill"
            :data-status="project.status"
          >
            {{
              project.summary?.stage
                ? stages[project.summary.stage] || project.summary.stage
                : labels[project.status] || project.status
            }}
          </el-tag>
        </div>

        <!-- Conteúdo do Card -->
        <div class="card-body">
          <div class="card-header-row">
            <AppButton class="project-title-link" @click.stop="$emit('open', project.id)">
              <h2 class="project-card-title">{{ project.title || project.name }}</h2>
            </AppButton>
          </div>

          <p class="project-source-info">
            {{
              project.is_manual
                ? 'Teste técnico de renderização'
                : project.has_transcript
                  ? `${project.word_count.toLocaleString('pt-BR')} palavras transcritas`
                  : project.name
            }}
          </p>

          <!-- Métricas inline limpas (sem cardception/chips) -->
          <div class="project-metrics-row">
            <span class="project-metrics-inline">
              {{ project.summary?.proposed ?? '—' }} propostas
              <template v-if="project.summary?.selected || project.summary?.generated">
                · <span class="highlight-count">{{ project.summary?.selected ?? 0 }} selecionados</span> · {{ project.summary?.generated ?? 0 }} prontos
              </template>
            </span>
          </div>
        </div>

        <!-- Rodapé do Card com Ações Rápidas -->
        <div class="card-footer">
          <span
            class="updated-time"
            :title="
              project.updated_at ? new Date(project.updated_at * 1000).toLocaleString('pt-BR') : ''
            "
          >
            {{ timeAgo(project.updated_at) }}
          </span>

          <div class="card-actions-group">
            <el-tooltip content="Excluir projeto permanentemente" placement="top">
              <AppButton
                type="button"
                class="icon-button delete-btn"
                data-action="delete-project"
                title="Excluir projeto permanentemente"
                :disabled="busy || activeProjects?.includes(project.id)"
                @click.stop="$emit('delete', project.id)"
              >
                <Trash2 :size="15" />
              </AppButton>
            </el-tooltip>
            <span class="open-card-indicator">Abrir →</span>
          </div>
        </div>
      </article>
    </section>

    <!-- ESTADO 2: TABELA ESTRUTURADA (Modo Denso com todas as classes mantidas) -->
    <section
      v-else-if="filtered.length && viewMode === 'list'"
      class="project-table"
      aria-label="Projetos locais"
    >
      <div class="table-head">
        <span>Projeto</span>
        <span>Duração</span>
        <span>Etapa / estado</span>
        <span>Cortes</span>
        <span>Atualizado</span>
        <span>Ações</span>
      </div>
      <div
        v-for="project in filtered"
        :key="project.id"
        class="project-row"
        :data-project-id="project.id"
        tabindex="0"
        role="button"
        :aria-label="'Abrir projeto: ' + (project.title || project.name)"
        @click="$emit('open', project.id)"
        @keydown.enter.prevent="$emit('open', project.id)"
        @keydown.space.prevent="$emit('open', project.id)"
      >
        <div class="project-name">
          <span class="video-thumb" :class="{ manual: project.is_manual }">
            <img
              v-if="covers?.[project.id] && brokenCovers[project.id] !== covers[project.id]"
              :src="covers[project.id]"
              alt=""
              loading="lazy"
              @error="brokenCovers[project.id] = covers?.[project.id] || ''"
            />
            <Film v-else :size="26" />
          </span>
          <div>
            <AppButton class="project-title-link" @click.stop="$emit('open', project.id)">
              <strong>{{ project.title || project.name }}</strong>
            </AppButton>
            <span>{{
              project.is_manual
                ? 'Teste de renderização'
                : project.has_transcript
                  ? `${project.word_count.toLocaleString('pt-BR')} palavras transcritas`
                  : project.name
            }}</span>
          </div>
        </div>

        <span class="table-duration">{{
          project.duration_us ? time(project.duration_us) : '—'
        }}</span>
        <span class="status-pill" :data-status="project.status">
          <i></i
          >{{
            project.summary?.stage
              ? stages[project.summary.stage] || project.summary.stage
              : labels[project.status] || project.status
          }}
        </span>
        <span class="project-counts">
          <span>{{
            project.summary?.proposed == null ? '—' : project.summary.proposed + ' propostas'
          }}</span>
          <small
            >{{
              project.summary?.selected == null ? '—' : project.summary.selected + ' selecionados'
            }}
            · {{ project.summary?.generated ?? '—' }} gerados</small
          >
        </span>
        <time
          class="project-updated"
          :title="
            project.updated_at ? new Date(project.updated_at * 1000).toLocaleString('pt-BR') : ''
          "
        >
          {{ updated(project.updated_at) }}
        </time>
        <AppButton
          type="button"
          class="icon-button"
          data-action="delete-project"
          title="Excluir projeto permanentemente"
          :disabled="busy || activeProjects?.includes(project.id)"
          @click.stop="$emit('delete', project.id)"
        >
          <Trash2 :size="16" />
        </AppButton>
      </div>
    </section>

    <!-- ESTADO 3: ESTADO VAZIO -->
    <section v-if="!filtered.length" class="empty-state studio-empty-state">
      <div class="empty-icon-wrap">
        <FileVideo :size="32" />
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
        @click="$emit('create')"
      >
        <Plus :size="16" />
        <span>Novo projeto</span>
      </AppButton>
    </section>
  </div>
</template>

<style scoped>
.library-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Barra de Ferramentas */
.library-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  background: var(--color-surface, #16191f);
  border: 1px solid var(--color-border-subtle, #2a303c);
  border-radius: 12px;
  padding: 10px 14px;
}
.search-box {
  position: relative;
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 260px;
}
.search-icon {
  position: absolute;
  left: 12px;
  color: var(--color-text-muted, #9aa4b2);
  pointer-events: none;
}
.search-box input {
  width: 100%;
  min-height: 38px;
  padding: 8px 34px 8px 36px;
  background: var(--color-canvas, #0e1013);
  border: 1px solid var(--color-border-subtle, #2a303c);
  border-radius: 8px;
  color: var(--color-text-primary, #f2f4f7);
  font-size: 0.88rem;
  transition: border-color 0.15s ease;
}
.search-box input:focus {
  outline: none;
  border-color: var(--color-border-strong);
}
.clear-search {
  position: absolute;
  right: 12px;
  color: var(--color-text-muted, #9aa4b2);
  cursor: pointer;
  font-size: 0.75rem;
}
.toolbar-controls {
  display: flex;
  align-items: center;
  gap: 14px;
}
.control-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.82rem;
  color: var(--color-text-muted, #9aa4b2);
}
.view-switcher {
  display: flex;
  align-items: center;
  background: var(--color-canvas, #0e1013);
  border: 1px solid var(--color-border-subtle, #2a303c);
  border-radius: 8px;
  padding: 2px;
  gap: 2px;
}
.view-btn {
  background: transparent;
  border: none;
  color: var(--color-text-muted, #9aa4b2);
  padding: 6px 8px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}
.view-btn.active {
  background: var(--color-surface-raised, #1e232b);
  color: var(--color-text-primary);
}

/* GRADE DE MÍDIA */
.projects-media-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}
.media-project-card {
  background: var(--color-surface, #16191f);
  border: 1px solid var(--color-border-subtle, #2a303c);
  border-radius: 14px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: all 0.2s ease;
}
.media-project-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-border-strong);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.4);
}
.card-thumbnail-wrap {
  position: relative;
  aspect-ratio: 16/9;
  background: var(--color-canvas, #0e1013);
  overflow: hidden;
}
.thumbnail-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.thumbnail-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted, #9aa4b2);
}
.video-duration-tag {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(14, 16, 19, 0.85);
  backdrop-filter: blur(4px);
  color: var(--color-text-primary, #f2f4f7);
  font-size: 0.72rem;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-variant-numeric: tabular-nums;
}
.card-status-pill {
  position: absolute;
  top: 8px;
  left: 8px;
  backdrop-filter: blur(4px);
}
.card-body {
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}
.project-title-link {
  padding: 0;
  text-align: left;
  border: none;
  background: transparent;
  color: var(--color-text-primary, #f2f4f7);
}
.project-card-title {
  font-size: 0.98rem;
  font-weight: 600;
  line-height: 1.35;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.project-source-info {
  font-size: 0.78rem;
  color: var(--color-text-muted, #9aa4b2);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.project-metrics-row {
  display: flex;
  margin-top: 4px;
}
.project-metrics-inline {
  font-size: 0.78rem;
  color: var(--color-text-muted, #9aa4b2);
  font-variant-numeric: tabular-nums;
}
.project-metrics-inline .highlight-count {
  color: var(--color-text-secondary);
  font-weight: 500;
}
.card-footer {
  padding: 10px 16px;
  border-top: 1px solid var(--color-border-subtle, #2a303c);
  background: rgba(14, 16, 19, 0.4);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.updated-time {
  font-size: 0.75rem;
  color: var(--color-text-muted, #9aa4b2);
}
.card-actions-group {
  display: flex;
  align-items: center;
  gap: 8px;
}
.open-card-indicator {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* Estado Vazio */
.studio-empty-state {
  background: var(--color-surface, #121518);
  border: 1px dashed var(--color-border-subtle, rgba(255, 255, 255, 0.06));
  border-radius: 12px;
  padding: 48px 24px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.empty-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: var(--color-surface-raised, #181b20);
  border: 1px solid var(--color-border-subtle, rgba(255, 255, 255, 0.06));
  color: var(--color-text-muted, #9aa4b2);
  display: flex;
  align-items: center;
  justify-content: center;
}
.studio-empty-state h2 {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text-primary, #f2f4f7);
  margin: 0;
  letter-spacing: -0.02em;
}
.studio-empty-state p {
  color: var(--color-text-muted, #9aa4b2);
  max-width: 44ch;
  margin: 0;
  font-size: 0.88rem;
}
.start-first-btn {
  font-weight: 500;
  padding: 8px 16px;
  margin-top: 4px;
}
</style>
