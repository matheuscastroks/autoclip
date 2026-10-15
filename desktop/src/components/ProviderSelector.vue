<script setup lang="ts">
import AppIcon from './ui/AppIcon.vue';
import { computed } from 'vue';

export type AiProvider = 'gemini' | 'openrouter';

const props = withDefaults(
  defineProps<{
    modelValue: AiProvider;
    disabled?: boolean;
    geminiConfigured?: boolean;
    openrouterConfigured?: boolean;
  }>(),
  {
    disabled: false,
    geminiConfigured: false,
    openrouterConfigured: false,
  }
);

const emit = defineEmits<{
  'update:modelValue': [provider: AiProvider];
}>();

function select(provider: AiProvider) {
  if (props.disabled) return;
  emit('update:modelValue', provider);
}
</script>

<template>
  <div class="provider-selector" role="radiogroup" aria-label="Provedor de inteligência artificial">
    <div
      class="provider-card"
      :class="{
        selected: modelValue === 'gemini',
        configured: geminiConfigured,
        disabled,
      }"
      role="radio"
      :aria-checked="modelValue === 'gemini'"
      tabindex="0"
      @click="select('gemini')"
      @keydown.space.prevent="select('gemini')"
      @keydown.enter.prevent="select('gemini')"
    >
      <div class="provider-icon">
        <AppIcon name="sparkle" size="md" />
      </div>
      <div class="provider-details">
        <div class="provider-title-row">
          <strong>Google Gemini</strong>
          <span v-if="geminiConfigured" class="configured-badge">Ativo</span>
        </div>
        <p class="provider-desc">Análise de vídeo nativa com multimodalidade e catálogo direto.</p>
      </div>
    </div>

    <div
      class="provider-card"
      :class="{
        selected: modelValue === 'openrouter',
        configured: openrouterConfigured,
        disabled,
      }"
      role="radio"
      :aria-checked="modelValue === 'openrouter'"
      tabindex="0"
      @click="select('openrouter')"
      @keydown.space.prevent="select('openrouter')"
      @keydown.enter.prevent="select('openrouter')"
    >
      <div class="provider-icon">
        <AppIcon name="globe" size="md" />
      </div>
      <div class="provider-details">
        <div class="provider-title-row">
          <strong>OpenRouter</strong>
          <span v-if="openrouterConfigured" class="configured-badge">Ativo</span>
        </div>
        <p class="provider-desc">
          Acesso flexível a múltiplos modelos e opções gratuitas/comunitárias.
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.provider-selector {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 14px;
}
.provider-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px;
  background: var(--surface, #1b1e26);
  border: 1px solid var(--line, rgba(255, 255, 255, 0.08));
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  outline: none;
}
.provider-card:hover:not(.disabled) {
  border-color: var(--color-border-strong);
  background: var(--color-surface-hover);
}
.provider-card:focus-visible {
  border-color: var(--color-border-strong);
  box-shadow: 0 0 0 2px var(--color-border-focus);
}
.provider-card.selected {
  border-color: var(--color-border-strong);
  background: var(--color-surface-selected);
}
.provider-icon {
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  background: var(--color-surface-selected);
  border-radius: 8px;
}
.provider-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.provider-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.provider-title-row strong {
  font-size: 14px;
  color: var(--ink, #f2f4f7);
}
.configured-badge {
  font-size: 11px;
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}
.provider-desc {
  font-size: 12px;
  color: var(--muted, #9aa4b2);
  margin: 0;
  line-height: 1.4;
}
.provider-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
