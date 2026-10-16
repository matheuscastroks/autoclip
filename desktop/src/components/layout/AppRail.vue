<script setup lang="ts">
import { ElTooltip } from 'element-plus';
import AppIcon from '../ui/AppIcon.vue';
import type { AppTheme } from '../../composables/useTheme';

withDefaults(
  defineProps<{
    activePage: 'projects' | 'settings';
    activeJobsCount: number;
    engineState: 'online' | 'offline' | 'checking';
    theme?: AppTheme;
  }>(),
  { theme: 'dark' }
);
defineEmits<{
  navigate: [page: 'projects' | 'settings'];
  openQueue: [];
  openEngineStatus: [];
  toggleTheme: [];
}>();
</script>

<template>
  <aside class="app-rail" aria-label="AutoClip">
    <span class="rail-brand" title="AutoClip"><AppIcon name="scissors" /></span>
    <nav aria-label="Navegação principal" class="rail-navigation">
      <ElTooltip content="Projetos" placement="right">
        <button
          class="rail-command"
          aria-label="Projetos"
          type="button"
          :aria-current="activePage === 'projects' ? 'page' : undefined"
          @click="$emit('navigate', 'projects')"
        >
          <AppIcon name="projects" :variant="activePage === 'projects' ? 'filled' : 'regular'" />
        </button>
      </ElTooltip>
      <ElTooltip content="Fila global de tarefas" placement="right">
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
          <span v-if="activeJobsCount > 0" class="rail-count" aria-hidden="true">{{
            activeJobsCount
          }}</span>
        </button>
      </ElTooltip>
    </nav>
    <div class="rail-bottom">
      <ElTooltip
        :content="theme === 'dark' ? 'Usar tema claro' : 'Usar tema escuro'"
        placement="right"
      >
        <button
          class="rail-command"
          :aria-label="theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro'"
          type="button"
          @click="$emit('toggleTheme')"
        >
          <AppIcon :name="theme === 'dark' ? 'sun' : 'moon'" />
        </button>
      </ElTooltip>
      <ElTooltip content="Configurações" placement="right">
        <button
          class="rail-command"
          aria-label="Configurações"
          type="button"
          :aria-current="activePage === 'settings' ? 'page' : undefined"
          @click="$emit('navigate', 'settings')"
        >
          <AppIcon name="settings" :variant="activePage === 'settings' ? 'filled' : 'regular'" />
        </button>
      </ElTooltip>
      <slot name="engine">
        <button
          class="rail-command"
          type="button"
          :aria-label="`Motor local: ${engineState === 'online' ? 'conectado' : engineState === 'offline' ? 'sem conexão' : 'conectando'}`"
          @click="$emit('openEngineStatus')"
        >
          <AppIcon name="engine" />
        </button>
      </slot>
    </div>
  </aside>
</template>

<style scoped>
.app-rail {
  width: 64px;
  flex: 0 0 64px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 12px 8px;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border-subtle);
  z-index: 20;
}
.rail-brand {
  height: 32px;
  display: grid;
  place-items: center;
  color: var(--color-text-primary);
}
.rail-navigation,
.rail-bottom {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.rail-bottom {
  margin-top: auto;
}
.rail-command {
  position: relative;
  display: grid;
  place-items: center;
  width: 44px;
  height: 40px;
  padding: 0;
  border: 1px solid transparent;
  border-radius: var(--radius-control);
  background: transparent;
  color: var(--color-text-secondary);
}
.rail-command:hover {
  background: var(--color-surface-hover);
  color: var(--color-text-primary);
}
.rail-command[aria-current] {
  background: var(--color-surface-selected);
  color: var(--color-text-primary);
  border-left-color: var(--color-action-primary);
}
.rail-count {
  position: absolute;
  top: -2px;
  right: -3px;
  min-width: 18px;
  padding: 0 3px;
  border-radius: 6px;
  background: var(--color-action-primary);
  color: var(--color-action-primary-text);
  font-size: 12px;
  line-height: 18px;
}
@media (forced-colors: active) {
  .rail-command[aria-current] {
    border-color: Highlight;
  }
}
</style>
