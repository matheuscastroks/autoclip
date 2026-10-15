<script setup lang="ts">
import AppButton from '../AppButton.vue';
import AppIcon from '../ui/AppIcon.vue';
defineProps<{ title: string; project?: boolean }>();
defineEmits<{ back: []; folder: [] }>();
</script>

<template>
  <header class="workspace-header" :class="{ 'project-heading': project }">
    <AppButton
      v-if="project"
      class="icon-button"
      aria-label="Todos os projetos"
      title="Todos os projetos"
      @click="$emit('back')"
      ><AppIcon name="back" size="sm"
    /></AppButton>
    <h1 :title="title">{{ title }}</h1>
    <div v-if="$slots.metadata" class="workspace-header-meta"><slot name="metadata" /></div>
    <div class="workspace-header-actions">
      <slot name="actions" />
      <AppButton
        v-if="project"
        class="icon-button"
        aria-label="Abrir pasta"
        title="Abrir pasta no Windows Explorer"
        @click="$emit('folder')"
        ><AppIcon name="folder-open" size="sm"
      /></AppButton>
    </div>
  </header>
</template>

<style scoped>
.workspace-header {
  min-height: 52px;
  flex: none;
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  min-width: 0;
}
h1 {
  font-size: var(--font-size-title);
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}
.workspace-header-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-meta);
  flex-shrink: 0;
}
.workspace-header-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
</style>
