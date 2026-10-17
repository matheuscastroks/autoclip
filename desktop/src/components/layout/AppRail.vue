<script setup lang="ts">
import { ref } from 'vue';
import { ElTooltip } from 'element-plus';
import AppIcon from '../ui/AppIcon.vue';
import type { AppTheme } from '../../composables/useTheme';

export type AppPage = 'projects' | 'all-cuts' | 'caption-styles' | 'exports' | 'settings';

const props = withDefaults(
  defineProps<{
    activePage: AppPage;
    activeJobsCount: number;
    pendingCutsCount?: number;
    exportedCount?: number;
    engineState: 'online' | 'offline' | 'checking';
    theme?: AppTheme;
    playbackSpeed?: '1x' | '1.25x' | '1.5x';
  }>(),
  { theme: 'dark', pendingCutsCount: 0, exportedCount: 0, playbackSpeed: '1x' }
);

const emit = defineEmits<{
  navigate: [page: AppPage];
  openQueue: [];
  openEngineStatus: [];
  toggleTheme: [];
  changeSpeed: [speed: '1x' | '1.25x' | '1.5x'];
}>();

const speeds: ('1x' | '1.25x' | '1.5x')[] = ['1x', '1.25x', '1.5x'];

function cycleSpeed() {
  const currentIndex = speeds.indexOf(props.playbackSpeed || '1x');
  const nextIndex = (currentIndex + 1) % speeds.length;
  emit('changeSpeed', speeds[nextIndex]);
}

const collapsed = ref(false);

function toggleCollapse() {
  collapsed.value = !collapsed.value;
  try {
    localStorage.setItem('autoclip-rail-collapsed', String(collapsed.value));
  } catch {}
}

try {
  const saved = localStorage.getItem('autoclip-rail-collapsed');
  if (saved !== null) {
    collapsed.value = saved === 'true';
  }
} catch {}
</script>

<template>
  <aside
    class="app-rail"
    :class="{ 'app-rail--collapsed': collapsed, 'app-rail--expanded': !collapsed }"
    aria-label="AutoClip"
  >
    <!-- Header: Logo, Nome do App e Botão de Recolher -->
    <div class="rail-header">
      <div
        class="rail-brand"
        title="AutoClip"
        :role="collapsed ? 'button' : undefined"
        :aria-label="collapsed ? 'Expandir barra lateral' : undefined"
        @click="collapsed ? toggleCollapse() : undefined"
      >
        <div class="brand-badge-icon">
          <AppIcon name="scissors" size="sm" />
        </div>
        <div v-if="!collapsed" class="brand-text">
          <span class="brand-title">AutoClip</span>
          <span class="brand-edition">Studio</span>
        </div>
      </div>
      <button
        v-if="!collapsed"
        class="rail-toggle-btn"
        title="Recolher barra lateral"
        aria-label="Recolher barra lateral"
        type="button"
        @click="toggleCollapse"
      >
        <svg
          class="toggle-chevron"
          viewBox="0 0 16 16"
          width="14"
          height="14"
          aria-hidden="true"
        >
          <path
            fill="none"
            stroke="currentColor"
            stroke-width="1.75"
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M10 3.5L5.5 8l4.5 4.5"
          />
        </svg>
      </button>
    </div>

    <!-- Navegação: Seção CRIAÇÃO -->
    <nav aria-label="Navegação de criação" class="rail-navigation">
      <div v-if="!collapsed" class="rail-section-header">Criação</div>

      <ElTooltip content="Projetos" placement="right" :disabled="!collapsed">
        <button
          class="rail-command"
          aria-label="Projetos"
          type="button"
          :aria-current="activePage === 'projects' ? 'page' : undefined"
          @click="$emit('navigate', 'projects')"
        >
          <AppIcon name="projects" :variant="activePage === 'projects' ? 'filled' : 'regular'" />
          <span v-if="!collapsed" class="rail-label">Projetos</span>
        </button>
      </ElTooltip>

      <ElTooltip content="Todos os Cortes" placement="right" :disabled="!collapsed">
        <button
          class="rail-command"
          aria-label="Todos os Cortes"
          type="button"
          :aria-current="activePage === 'all-cuts' ? 'page' : undefined"
          @click="$emit('navigate', 'all-cuts')"
        >
          <AppIcon name="scissors" />
          <span v-if="!collapsed" class="rail-label">Todos os Cortes</span>
          <span
            v-if="pendingCutsCount > 0"
            class="rail-count rail-count--pending"
            title="Cortes pendentes de revisão"
          >
            {{ pendingCutsCount }}
          </span>
        </button>
      </ElTooltip>
    </nav>

    <!-- Navegação: Seção ESTÚDIO -->
    <nav aria-label="Navegação de estúdio" class="rail-navigation rail-navigation--studio">
      <div v-if="!collapsed" class="rail-section-header">Estúdio</div>

      <ElTooltip content="Estilos de Legenda" placement="right" :disabled="!collapsed">
        <button
          class="rail-command"
          aria-label="Estilos de Legenda"
          type="button"
          :aria-current="activePage === 'caption-styles' ? 'page' : undefined"
          @click="$emit('navigate', 'caption-styles')"
        >
          <AppIcon name="sparkle" />
          <span v-if="!collapsed" class="rail-label">Estilos de Legenda</span>
        </button>
      </ElTooltip>

      <ElTooltip content="Central de Exportações" placement="right" :disabled="!collapsed">
        <button
          class="rail-command"
          aria-label="Central de Exportações"
          type="button"
          :aria-current="activePage === 'exports' ? 'page' : undefined"
          @click="$emit('navigate', 'exports')"
        >
          <AppIcon name="download" />
          <span v-if="!collapsed" class="rail-label">Exportações</span>
          <span
            v-if="exportedCount > 0"
            class="rail-count rail-count--exported"
            title="Vídeos exportados"
          >
            {{ exportedCount }}
          </span>
        </button>
      </ElTooltip>

      <!-- Velocidade dos Vídeos -->
      <div v-if="!collapsed" class="rail-speed-box">
        <div class="rail-speed-meta">
          <span class="rail-speed-title">Velocidade</span>
          <span class="rail-speed-value">{{ playbackSpeed }}</span>
        </div>
        <div class="rail-speed-pills" role="radiogroup" aria-label="Velocidade de exportação">
          <button
            v-for="s in speeds"
            :key="s"
            type="button"
            role="radio"
            :aria-checked="playbackSpeed === s"
            class="rail-speed-pill"
            :class="{ 'is-active': playbackSpeed === s }"
            :title="`Exportar em velocidade ${s}`"
            @click="$emit('changeSpeed', s)"
          >
            {{ s }}
          </button>
        </div>
      </div>
      <ElTooltip
        v-else
        :content="`Velocidade de exportação: ${playbackSpeed} (clique para alternar)`"
        placement="right"
      >
        <button
          class="rail-command rail-command--speed"
          :aria-label="`Velocidade de exportação: ${playbackSpeed}`"
          type="button"
          @click="cycleSpeed"
        >
          <span class="rail-speed-mini-badge">{{ playbackSpeed }}</span>
        </button>
      </ElTooltip>
    </nav>

    <!-- Rodapé: Seção SISTEMA -->
    <div class="rail-bottom">
      <div v-if="!collapsed" class="rail-section-header">Sistema</div>

      <ElTooltip content="Fila global de tarefas" placement="right" :disabled="!collapsed">
        <button
          class="rail-command"
          :aria-label="
            activeJobsCount > 0
              ? `Fila global de tarefas · ${activeJobsCount} tarefas ativas`
              : 'Fila global de tarefas'
          "
          title="Fila global de tarefas"
          type="button"
          @click="$emit('openQueue')"
        >
          <AppIcon name="queue" />
          <span v-if="!collapsed" class="rail-label">Fila de tarefas</span>
          <span v-if="activeJobsCount > 0" class="rail-count" aria-hidden="true">{{
            activeJobsCount
          }}</span>
        </button>
      </ElTooltip>

      <ElTooltip
        :content="theme === 'dark' ? 'Usar tema claro' : 'Usar tema escuro'"
        placement="right"
        :disabled="!collapsed"
      >
        <button
          class="rail-command"
          :aria-label="theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro'"
          type="button"
          @click="$emit('toggleTheme')"
        >
          <AppIcon :name="theme === 'dark' ? 'sun' : 'moon'" />
          <span v-if="!collapsed" class="rail-label">{{
            theme === 'dark' ? 'Modo claro' : 'Modo escuro'
          }}</span>
        </button>
      </ElTooltip>

      <ElTooltip content="Configurações" placement="right" :disabled="!collapsed">
        <button
          class="rail-command"
          aria-label="Configurações"
          type="button"
          :aria-current="activePage === 'settings' ? 'page' : undefined"
          @click="$emit('navigate', 'settings')"
        >
          <AppIcon name="settings" :variant="activePage === 'settings' ? 'filled' : 'regular'" />
          <span v-if="!collapsed" class="rail-label">Configurações</span>
        </button>
      </ElTooltip>

      <slot name="engine" :collapsed="collapsed">
        <button
          class="rail-command"
          type="button"
          :aria-label="`Motor local: ${engineState === 'online' ? 'conectado' : engineState === 'offline' ? 'sem conexão' : 'conectando'}`"
          @click="$emit('openEngineStatus')"
        >
          <AppIcon name="engine" />
          <span v-if="!collapsed" class="rail-label">Motor local</span>
        </button>
      </slot>
    </div>
  </aside>
</template>

<style scoped>
.app-rail {
  width: 220px;
  flex: 0 0 220px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 14px 12px;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border-subtle);
  z-index: 20;
  transition: width 0.22s cubic-bezier(0.32, 0.72, 0, 1),
              flex-basis 0.22s cubic-bezier(0.32, 0.72, 0, 1),
              padding 0.22s cubic-bezier(0.32, 0.72, 0, 1);
  overflow-y: auto;
  overflow-x: hidden;
  user-select: none;
}

.app-rail--collapsed {
  width: 64px;
  flex: 0 0 64px;
  padding: 14px 8px;
  align-items: center;
}

.rail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 2px 4px 6px;
  min-height: 36px;
}

.app-rail--collapsed .rail-header {
  justify-content: center;
  padding: 2px 0 6px;
}

.rail-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--color-text-primary);
  text-decoration: none;
  min-width: 0;
}

.brand-badge-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-action-primary);
  flex-shrink: 0;
  transition: transform 0.15s ease, border-color 0.15s ease;
}

.rail-brand:hover .brand-badge-icon {
  border-color: var(--color-border-strong);
  transform: scale(1.04);
}

.brand-text {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.brand-title {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--color-text-primary);
  white-space: nowrap;
}

.brand-edition {
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 2px 5px;
  border-radius: 4px;
  background: rgba(175, 198, 213, 0.12);
  color: var(--color-action-primary);
  border: 1px solid rgba(175, 198, 213, 0.25);
  line-height: 1;
}

.rail-toggle-btn {
  width: 26px;
  height: 26px;
  border-radius: var(--radius-control);
  background: transparent;
  border: 1px solid transparent;
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 0;
  transition: all 0.15s ease;
}

.rail-toggle-btn:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-border-subtle);
  color: var(--color-text-primary);
}

.app-rail--collapsed .rail-toggle-btn {
  display: none;
}

.app-rail--collapsed .rail-brand {
  cursor: pointer;
}

.toggle-chevron {
  transition: transform 0.2s cubic-bezier(0.32, 0.72, 0, 1);
}

.rail-section-header {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-muted);
  padding: 6px 10px 4px;
}

.rail-navigation {
  display: flex;
  flex-direction: column;
  gap: 3px;
  width: 100%;
}

.rail-navigation--studio {
  margin-top: 4px;
}

.rail-bottom {
  margin-top: auto;
  padding-top: 10px;
  border-top: 1px solid var(--color-border-subtle);
  display: flex;
  flex-direction: column;
  gap: 3px;
  width: 100%;
}

.rail-command {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  height: 38px;
  padding: 0 10px;
  border: 1px solid transparent;
  border-radius: var(--radius-control);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.app-rail--collapsed .rail-command {
  width: 44px;
  height: 40px;
  padding: 0;
  justify-content: center;
}

.rail-command:hover {
  background: var(--color-surface-hover);
  color: var(--color-text-primary);
}

.rail-command[aria-current] {
  background: var(--color-surface-selected);
  color: var(--color-text-primary);
  border-color: rgba(175, 198, 213, 0.25);
  font-weight: 600;
}

.rail-label {
  flex: 1;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rail-count {
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: var(--color-action-primary);
  color: var(--color-action-primary-text);
  font-size: 11px;
  font-weight: 700;
  line-height: 18px;
  text-align: center;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.rail-count--pending {
  background: var(--color-warning-surface);
  color: var(--color-warning-text);
  border: 1px solid var(--color-warning-border);
}

.rail-count--exported {
  background: var(--color-success-soft);
  color: var(--color-success);
  border: 1px solid var(--color-success-border);
}

.app-rail--collapsed .rail-count {
  position: absolute;
  top: 1px;
  right: 2px;
}

/* Widget de Velocidade na Barra Lateral */
.rail-speed-box {
  margin-top: 6px;
  padding: 8px 10px;
  background: var(--color-surface-raised, rgba(255, 255, 255, 0.03));
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-control);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rail-speed-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.rail-speed-title {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.rail-speed-value {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-action-primary);
  font-feature-settings: 'tnum';
}

.rail-speed-pills {
  display: flex;
  background: var(--color-canvas);
  border: 1px solid var(--color-border-subtle);
  border-radius: 6px;
  padding: 2px;
  gap: 2px;
}

.rail-speed-pill {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 11px;
  font-weight: 600;
  padding: 4px 0;
  border-radius: 4px;
  cursor: pointer;
  text-align: center;
  transition: all 0.12s ease;
  outline: none;
}

.rail-speed-pill:hover {
  color: var(--color-text-primary);
  background: var(--color-surface-hover);
}

.rail-speed-pill.is-active {
  background: var(--color-action-primary);
  color: var(--color-action-primary-text, #ffffff);
}

.rail-speed-mini-badge {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-primary);
  font-feature-settings: 'tnum';
  border: 1px solid var(--color-border-subtle);
  border-radius: 4px;
  padding: 2px 4px;
  background: var(--color-surface-raised);
}

@media (forced-colors: active) {
  .rail-command[aria-current] {
    border-color: Highlight;
  }
}
</style>
