<script setup lang="ts">
import AppIcon from './ui/AppIcon.vue';
import { onMounted, onUnmounted, ref } from 'vue';

const props = withDefaults(
  defineProps<{
    title?: string;
    ariaLabel?: string;
    maxWidth?: string;
  }>(),
  {
    title: '',
    ariaLabel: 'Diálogo modal',
    maxWidth: '680px',
  }
);

const emit = defineEmits<{
  close: [];
}>();

const modalRef = ref<HTMLDivElement>();
let previousActiveElement: HTMLElement | null = null;

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    emit('close');
  }
}

onMounted(() => {
  if (typeof document !== 'undefined') {
    previousActiveElement = document.activeElement as HTMLElement | null;
    modalRef.value?.focus();
  }
});

onUnmounted(() => {
  previousActiveElement?.focus();
});
</script>

<template>
  <div
    class="base-modal-overlay"
    role="dialog"
    aria-modal="true"
    :aria-label="ariaLabel || title"
    tabindex="-1"
    @keydown="handleKeydown"
    @click.self="$emit('close')"
  >
    <div ref="modalRef" class="base-modal-container" :style="{ maxWidth }" tabindex="0">
      <header v-if="title || $slots.header" class="base-modal-header">
        <slot name="header">
          <h2 class="base-modal-title">{{ title }}</h2>
        </slot>
        <button
          type="button"
          class="base-modal-close-btn"
          aria-label="Fechar modal"
          @click="$emit('close')"
        >
          <AppIcon name="close" size="md" />
        </button>
      </header>

      <div class="base-modal-body">
        <slot></slot>
      </div>

      <footer v-if="$slots.footer" class="base-modal-footer">
        <slot name="footer"></slot>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.base-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
}
.base-modal-container {
  background: var(--panel, #16191f);
  border: 1px solid var(--line, rgba(255, 255, 255, 0.1));
  border-radius: 12px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.5);
  outline: none;
}
.base-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--line, rgba(255, 255, 255, 0.08));
}
.base-modal-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--ink, #f2f4f7);
}
.base-modal-close-btn {
  background: transparent;
  border: none;
  color: var(--muted, #9aa4b2);
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.base-modal-close-btn:hover {
  color: var(--ink, #ffffff);
  background: rgba(255, 255, 255, 0.05);
}
.base-modal-body {
  padding: 16px 20px;
  overflow-y: auto;
}
.base-modal-footer {
  padding: 14px 20px;
  border-top: 1px solid var(--line, rgba(255, 255, 255, 0.08));
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}
</style>
