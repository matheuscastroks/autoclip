<script setup lang="ts">
import { computed, ref } from 'vue';
import type { Project, Revision } from '../types';
import AppButton from './AppButton.vue';
import AppSelect from './AppSelect.vue';
import AppIcon from './ui/AppIcon.vue';
import StatusTag from './StatusTag.vue';
import { isFinalAvailable, isPreviewAvailable } from '../domain/revisionPresentation';

export interface EnrichedCut {
  revision: Revision;
  project: Project;
  previewUrl?: string;
}

const props = defineProps<{
  cuts: EnrichedCut[];
  loading?: boolean;
}>();

const emit = defineEmits<{
  inspect: [cut: EnrichedCut];
  export: [cut: EnrichedCut];
  openProject: [projectId: string];
}>();

const filterTab = ref<'all' | 'pending' | 'approved' | 'exported'>('all');
const searchQuery = ref('');
const selectedProjectId = ref<string>('all');
const viewMode = ref<'list' | 'grid'>('list');

const uniqueProjects = computed(() => {
  const map = new Map<string, Project>();
  for (const c of props.cuts) {
    if (!map.has(c.project.id)) map.set(c.project.id, c.project);
  }
  return Array.from(map.values());
});

const projectOptions = computed(() => [
  { value: 'all', label: 'Todos os Projetos' },
  ...uniqueProjects.value.map(p => ({
    value: p.id,
    label: p.title || p.name,
  })),
]);

const counts = computed(() => {
  let pending = 0;
  let approved = 0;
  let exported = 0;

  for (const c of props.cuts) {
    if (c.revision.exported) {
      exported++;
    } else if (c.revision.review_status === 'approved') {
      approved++;
    } else {
      pending++;
    }
  }

  return { total: props.cuts.length, pending, approved, exported };
});

const filteredCuts = computed(() => {
  return props.cuts.filter(item => {
    // Tab filter
    if (filterTab.value === 'pending' && (item.revision.review_status === 'approved' || item.revision.exported)) return false;
    if (filterTab.value === 'approved' && (item.revision.review_status !== 'approved' || item.revision.exported)) return false;
    if (filterTab.value === 'exported' && !item.revision.exported) return false;

    // Project filter
    if (selectedProjectId.value !== 'all' && item.project.id !== selectedProjectId.value) return false;

    // Search query
    if (searchQuery.value.trim()) {
      const q = searchQuery.value.toLowerCase();
      const title = (item.revision.title || '').toLowerCase();
      const projName = (item.project.title || item.project.name || '').toLowerCase();
      return title.includes(q) || projName.includes(q);
    }

    return true;
  });
});

function formatDuration(us: number): string {
  const sec = Math.round(us / 1_000_000);
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}
</script>

<template>
  <div class="all-cuts-view">
    <header class="cuts-header">
      <div class="header-titles">
        <h1 class="view-title">Todos os Cortes</h1>
        <p class="view-subtitle">
          Gerencie, revise e aprove cortes de todos os seus projetos em um só lugar.
        </p>
      </div>

      <!-- Métricas Rápidas -->
      <div class="cuts-metrics">
        <div class="metric-chip">
          <span class="metric-value">{{ counts.total }}</span>
          <span class="metric-label">Total</span>
        </div>
        <div class="metric-chip highlight-pending">
          <span class="metric-value">{{ counts.pending }}</span>
          <span class="metric-label">Pendentes</span>
        </div>
        <div class="metric-chip highlight-approved">
          <span class="metric-value">{{ counts.approved }}</span>
          <span class="metric-label">Aprovados</span>
        </div>
        <div class="metric-chip highlight-exported">
          <span class="metric-value">{{ counts.exported }}</span>
          <span class="metric-label">Exportados</span>
        </div>
      </div>
    </header>

    <!-- Barra de Filtros e Busca -->
    <div class="cuts-toolbar">
      <div class="tabs-group" role="tablist">
        <button
          type="button"
          class="tab-btn"
          :class="{ active: filterTab === 'all' }"
          @click="filterTab = 'all'"
        >
          Todos <span class="tab-badge">{{ counts.total }}</span>
        </button>
        <button
          type="button"
          class="tab-btn"
          :class="{ active: filterTab === 'pending' }"
          @click="filterTab = 'pending'"
        >
          Pendentes <span class="tab-badge">{{ counts.pending }}</span>
        </button>
        <button
          type="button"
          class="tab-btn"
          :class="{ active: filterTab === 'approved' }"
          @click="filterTab = 'approved'"
        >
          Aprovados <span class="tab-badge">{{ counts.approved }}</span>
        </button>
        <button
          type="button"
          class="tab-btn"
          :class="{ active: filterTab === 'exported' }"
          @click="filterTab = 'exported'"
        >
          Exportados <span class="tab-badge">{{ counts.exported }}</span>
        </button>
      </div>

      <div class="filters-group">
        <div class="search-input-wrapper">
          <AppIcon name="search" size="sm" class="search-icon" />
          <input
            v-model="searchQuery"
            type="search"
            placeholder="Buscar por título ou projeto…"
            class="search-input"
          />
        </div>

        <AppSelect
          v-if="uniqueProjects.length > 1"
          v-model="selectedProjectId"
          :options="projectOptions"
          label="Filtrar por projeto"
          class="project-filter-select"
        />

        <div class="view-mode-toggle" role="group" aria-label="Modo de visualização">
          <button
            type="button"
            class="view-mode-btn"
            :class="{ active: viewMode === 'list' }"
            aria-label="Visualização em lista"
            title="Lista com detalhes e ação"
            @click="viewMode = 'list'"
          >
            <AppIcon name="list" size="sm" />
          </button>
          <button
            type="button"
            class="view-mode-btn"
            :class="{ active: viewMode === 'grid' }"
            aria-label="Visualização em grade"
            title="Grade de miniaturas"
            @click="viewMode = 'grid'"
          >
            <AppIcon name="grid" size="sm" />
          </button>
        </div>
      </div>
    </div>

    <!-- Modo 1: Lista de Trabalho (Padrão Desktop) -->
    <div v-if="filteredCuts.length && viewMode === 'list'" class="cuts-list-container">
      <table class="cuts-table">
        <thead>
          <tr>
            <th class="th-thumb">Miniatura</th>
            <th class="th-title">Corte & Projeto</th>
            <th class="th-duration">Duração</th>
            <th class="th-status">Estado</th>
            <th class="th-action">Próxima Ação</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in filteredCuts"
            :key="item.revision.revision_id"
            class="cut-table-row"
            :class="{
              'row--approved': item.revision.review_status === 'approved',
              'row--exported': item.revision.exported,
            }"
            @click="$emit('inspect', item)"
          >
            <td class="td-thumb">
              <div class="table-thumb-box">
                <img v-if="item.previewUrl" :src="item.previewUrl" alt="" class="table-thumb-img" />
                <div v-else class="table-thumb-placeholder">
                  <AppIcon name="video" size="sm" />
                </div>
              </div>
            </td>
            <td class="td-title">
              <div class="cut-titles-cell">
                <strong class="cut-main-title">{{ item.revision.title || 'Corte sem título' }}</strong>
                <span class="cut-project-subtitle">{{ item.project.title || item.project.name }}</span>
              </div>
            </td>
            <td class="td-duration">
              <span class="cut-duration-pill">{{ formatDuration(item.revision.duration_us ?? 0) }}</span>
            </td>
            <td class="td-status">
              <StatusTag :status="item.revision.review_status || 'needs_review'" />
            </td>
            <td class="td-action" @click.stop>
              <AppButton
                class="button small primary action-table-btn"
                @click="$emit('inspect', item)"
              >
                {{
                  item.revision.exported
                    ? 'Consultar'
                    : item.revision.review_status === 'approved'
                      ? 'Exportar'
                      : isFinalAvailable(item.revision)
                        ? 'Revisar 5 critérios'
                        : 'Avaliar prévia'
                }}
              </AppButton>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modo 2: Grade de Miniaturas 9:16 -->
    <div v-else-if="filteredCuts.length && viewMode === 'grid'" class="cuts-grid">
      <article
        v-for="item in filteredCuts"
        :key="item.revision.revision_id"
        class="cut-card"
        :class="{
          'cut-card--approved': item.revision.review_status === 'approved',
          'cut-card--exported': item.revision.exported,
        }"
        @click="$emit('inspect', item)"
      >
        <div class="card-media-preview">
          <!-- Badge editorial posicionado no canto superior esquerdo da imagem -->
          <div class="card-status-badge-overlay">
            <StatusTag :status="item.revision.review_status || 'needs_review'" />
          </div>

          <div class="ratio-box">
            <img
              v-if="item.previewUrl"
              :src="item.previewUrl"
              class="cut-thumb-img"
              loading="lazy"
              alt=""
            />
            <div v-else class="placeholder-916">
              <AppIcon name="video" size="lg" />
              <span class="preview-badge" v-if="isPreviewAvailable(item.revision)">Prévia pronta</span>
              <span class="final-badge" v-if="isFinalAvailable(item.revision)">Final renderizado</span>
            </div>
          </div>
          <span class="duration-badge">{{ formatDuration(item.revision.duration_us ?? 0) }}</span>
        </div>

        <div class="card-content">
          <div class="card-meta-top">
            <button
              type="button"
              class="project-origin-tag"
              title="Ir para este projeto"
              @click.stop="$emit('openProject', item.project.id)"
            >
              <AppIcon name="projects" size="sm" />
              <span>{{ item.project.title || item.project.name }}</span>
            </button>
          </div>

          <h3 class="cut-title">
            {{ item.revision.title || 'Corte sem título' }}
          </h3>

          <div class="card-footer-actions" @click.stop>
            <AppButton
              class="button small secondary inspect-btn"
              @click="$emit('inspect', item)"
            >
              <AppIcon name="eye" size="sm" />
              Inspecionar
            </AppButton>

            <AppButton
              v-if="item.revision.review_status === 'approved' && !item.revision.exported"
              class="button small primary export-btn"
              @click="$emit('export', item)"
            >
              <AppIcon name="download" size="sm" />
              Exportar
            </AppButton>
          </div>
        </div>
      </article>
    </div>

    <!-- Estado Vazio -->
    <div v-else class="cuts-empty-state">
      <div class="empty-icon-wrap">
        <AppIcon name="scissors" size="lg" />
      </div>
      <h3>Nenhum corte encontrado</h3>
      <p v-if="searchQuery">
        Nenhum corte corresponde à busca "{{ searchQuery }}". Tente outros termos.
      </p>
      <p v-else-if="filterTab !== 'all'">
        Nenhum corte neste filtro ({{ filterTab }}).
      </p>
      <p v-else>
        Gere cortes a partir de vídeos importados na aba Projetos para vê-los centralizados aqui.
      </p>
    </div>
  </div>
</template>

<style scoped>
.all-cuts-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 32px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.cuts-header {
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
}

.cuts-metrics {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.metric-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 14px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-control);
  min-width: 75px;
}

.metric-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.2;
}

.metric-label {
  font-size: 11px;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.highlight-pending .metric-value {
  color: var(--color-warning-text);
}

.highlight-approved .metric-value {
  color: var(--color-action-primary);
}

.highlight-exported .metric-value {
  color: var(--color-success);
}

/* Toolbar */
.cuts-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.tabs-group {
  display: flex;
  background: var(--color-canvas);
  padding: 3px;
  border-radius: 8px;
  border: 1px solid var(--color-border-subtle);
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 500;
  border-radius: 6px;
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.tab-btn:hover {
  color: var(--color-text-primary);
}

.tab-btn.active {
  background: var(--color-surface-raised);
  color: var(--color-text-primary);
  font-weight: 600;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

.tab-badge {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 999px;
  background: var(--color-surface);
  color: var(--color-text-muted);
}

.tab-btn.active .tab-badge {
  background: var(--color-surface-hover);
  color: var(--color-text-primary);
}

.filters-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 10px;
  color: var(--color-text-muted);
  pointer-events: none;
}

.search-input {
  height: 34px;
  padding: 0 12px 0 32px;
  border-radius: var(--radius-control);
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  color: var(--color-text-primary);
  font-size: 13px;
  min-width: 240px;
  transition: border-color 0.15s ease;
}

.search-input:focus {
  border-color: var(--color-action-primary);
  outline: none;
}

.project-filter-select {
  height: 34px;
  padding: 0 12px;
  border-radius: var(--radius-control);
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  color: var(--color-text-primary);
  font-size: 13px;
  cursor: pointer;
  outline: none;
}

/* Grid */
.cuts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.cut-card {
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.cut-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-border-strong);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
}

.cut-card--approved {
  border-color: rgba(175, 198, 213, 0.35);
}

.cut-card--exported {
  border-color: rgba(52, 211, 153, 0.3);
}

.card-media-preview {
  position: relative;
  background: var(--color-canvas);
  border-bottom: 1px solid var(--color-border-subtle);
  overflow: hidden;
}

.card-status-badge-overlay {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 3;
}

.cut-thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.ratio-box {
  width: 100%;
  aspect-ratio: 16 / 9;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.placeholder-916 {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--color-text-muted);
}

.preview-badge,
.final-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
}

.preview-badge {
  background: rgba(175, 198, 213, 0.15);
  color: var(--color-action-primary);
}

.final-badge {
  background: rgba(52, 211, 153, 0.15);
  color: var(--color-success);
}

.duration-badge {
  position: absolute;
  bottom: 8px;
  right: 8px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(16, 19, 22, 0.85);
  backdrop-filter: blur(4px);
  color: var(--color-text-primary);
  font-size: 11px;
  font-weight: 600;
  font-family: ui-monospace, monospace;
}

.card-content {
  display: flex;
  flex-direction: column;
  padding: 16px;
  gap: 12px;
  flex: 1;
}

.card-meta-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.project-origin-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
  border-radius: 4px;
  color: var(--color-text-secondary);
  font-size: 11px;
  padding: 2px 7px;
  cursor: pointer;
  transition: all 0.15s ease;
  max-width: 140px;
}

.project-origin-tag span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-origin-tag:hover {
  color: var(--color-text-primary);
  border-color: var(--color-border-strong);
}

.cut-title {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--color-text-primary);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 38px;
}

.card-footer-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: auto;
  padding-top: 8px;
}

/* Empty State */
.cuts-empty-state {
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

.cuts-empty-state h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 8px;
}

.cuts-empty-state p {
  font-size: 13px;
  color: var(--color-text-secondary);
  max-width: 420px;
  margin: 0;
}

/* View Mode Toggle */
.view-mode-toggle {
  display: inline-flex;
  align-items: center;
  background: var(--color-surface-raised, #202226);
  border: 1px solid var(--color-border-subtle, rgba(255, 255, 255, 0.08));
  border-radius: var(--radius-control, 8px);
  padding: 2px;
  gap: 2px;
  margin-left: 8px;
}

.view-mode-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--color-text-secondary, #94a3b8);
  cursor: pointer;
  transition: all 0.15s ease;
}

.view-mode-btn:hover {
  color: var(--color-text-primary, #f8fafc);
}

.view-mode-btn.active {
  background: var(--color-surface, #18191c);
  color: var(--color-action-primary, #60a5fa);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

/* Cuts Table List View */
.cuts-list-container {
  width: 100%;
  background: var(--color-surface, #18191c);
  border: 1px solid var(--color-border-subtle, rgba(255, 255, 255, 0.08));
  border-radius: var(--radius-panel, 12px);
  overflow: hidden;
}

.cuts-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.cuts-table th {
  padding: 12px 16px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary, #94a3b8);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  background: var(--color-surface-raised, #202226);
  border-bottom: 1px solid var(--color-border-subtle, rgba(255, 255, 255, 0.08));
}

.cut-table-row {
  cursor: pointer;
  border-bottom: 1px solid var(--color-border-subtle, rgba(255, 255, 255, 0.06));
  transition: background 0.15s ease;
}

.cut-table-row:hover {
  background: rgba(255, 255, 255, 0.03);
}

.cut-table-row td {
  padding: 10px 16px;
  vertical-align: middle;
}

.th-thumb, .td-thumb {
  width: 52px;
  padding-right: 8px;
}

.table-thumb-box {
  width: 36px;
  height: 64px;
  border-radius: 6px;
  overflow: hidden;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.table-thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.table-thumb-placeholder {
  color: var(--color-text-muted, #64748b);
  display: flex;
  align-items: center;
  justify-content: center;
}

.cut-titles-cell {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.cut-main-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary, #f8fafc);
  line-height: 1.3;
}

.cut-project-subtitle {
  font-size: 12px;
  color: var(--color-text-secondary, #94a3b8);
}

.cut-duration-pill {
  font-size: 12px;
  font-family: var(--font-mono, monospace);
  padding: 2px 8px;
  border-radius: 6px;
  background: var(--color-canvas, #0f1012);
  color: var(--color-text-secondary, #94a3b8);
  border: 1px solid var(--color-border-subtle, rgba(255, 255, 255, 0.06));
}

.th-action, .td-action {
  text-align: right;
  width: 170px;
}
</style>
