<script setup lang="ts">
import AppButton from '../AppButton.vue';
import AppIcon from '../ui/AppIcon.vue';
import type { IconName } from '../ui/icons';
export type ProjectTab = 'overview' | 'transcript' | 'analysis' | 'cuts';
const props = defineProps<{
  modelValue: ProjectTab;
  counts?: Partial<Record<ProjectTab, number>>;
  completed?: Partial<Record<ProjectTab, boolean>>;
}>();
const emit = defineEmits<{ 'update:modelValue': [value: ProjectTab] }>();
const tabs: { id: ProjectTab; label: string; icon: IconName }[] = [
  { id: 'overview', label: 'Preparação', icon: 'play' },
  { id: 'transcript', label: 'Transcrição', icon: 'transcript' },
  { id: 'analysis', label: 'Análise', icon: 'search' },
  { id: 'cuts', label: 'Cortes', icon: 'scissors' },
];
function tabKey(event: KeyboardEvent) {
  const at = tabs.findIndex(t => t.id === props.modelValue);
  const next =
    event.key === 'ArrowRight'
      ? (at + 1) % tabs.length
      : event.key === 'ArrowLeft'
        ? (at + tabs.length - 1) % tabs.length
        : event.key === 'Home'
          ? 0
          : event.key === 'End'
            ? tabs.length - 1
            : -1;
  if (next < 0) return;
  event.preventDefault();
  emit('update:modelValue', tabs[next].id);
  (event.currentTarget as HTMLElement)
    .querySelectorAll<HTMLButtonElement>('[role=tab]')
    [next]?.focus();
}
</script>

<template>
  <div class="project-tabs" role="tablist" aria-label="Áreas do projeto" @keydown="tabKey">
    <AppButton
      v-for="t in tabs"
      :key="t.id"
      :id="'tab-' + t.id"
      role="tab"
      aria-controls="project-panel"
      :tabindex="modelValue === t.id ? 0 : -1"
      :aria-selected="modelValue === t.id"
      :class="{ selected: modelValue === t.id, 'is-completed': completed?.[t.id] }"
      @click="$emit('update:modelValue', t.id)"
    >
      <AppIcon :name="t.icon" size="sm" />
      <span>{{ t.label }}</span>
      <span v-if="counts?.[t.id] !== undefined" class="tab-count">{{ counts[t.id]?.toLocaleString('pt-BR') }}</span>
      <span
        v-if="completed?.[t.id]"
        class="tab-completed-badge"
        data-tab-completed
        :title="`${t.label} concluída`"
      >
        <AppIcon name="check" size="sm" />
      </span>
    </AppButton>
  </div>
</template>

<style scoped>
.tab-completed-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--color-success, #34d399) !important;
  margin-left: 2px;
}
.tab-completed-badge :deep(svg) {
  width: 13px;
  height: 13px;
}
</style>
