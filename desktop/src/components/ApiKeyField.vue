<script setup lang="ts">
import { ref } from 'vue';
import { KeyRound, Eye, EyeOff } from '@lucide/vue';
import AppButton from './AppButton.vue';

const props = withDefaults(
  defineProps<{
    modelValue: string;
    placeholder?: string;
    label?: string;
    busy?: boolean;
    buttonText?: string;
    disabled?: boolean;
  }>(),
  {
    placeholder: 'Insira sua chave...',
    label: 'Chave de API',
    busy: false,
    buttonText: 'Salvar Chave',
    disabled: false,
  }
);

const emit = defineEmits<{
  'update:modelValue': [value: string];
  save: [];
}>();

const showPassword = ref(false);

function handleInput(e: Event) {
  emit('update:modelValue', (e.target as HTMLInputElement).value);
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    e.preventDefault();
    emit('save');
  }
}
</script>

<template>
  <div class="api-key-field">
    <label v-if="label" class="field-label">{{ label }}</label>
    <div class="input-action-wrapper">
      <div class="input-container">
        <input
          :type="showPassword ? 'text' : 'password'"
          :value="modelValue"
          :placeholder="placeholder"
          :disabled="busy || disabled"
          class="key-input"
          autocomplete="new-password"
          spellcheck="false"
          autocapitalize="off"
          data-1p-ignore
          @input="handleInput"
          @keydown="handleKeydown"
        />
        <button
          type="button"
          class="toggle-visibility-btn"
          :aria-label="showPassword ? 'Ocultar chave' : 'Mostrar chave'"
          @click="showPassword = !showPassword"
        >
          <EyeOff v-if="showPassword" :size="16" />
          <Eye v-else :size="16" />
        </button>
      </div>

      <AppButton
        type="button"
        class="button primary save-key-btn"
        :disabled="busy || disabled || !modelValue.trim()"
        @click="$emit('save')"
      >
        <KeyRound :size="15" />
        <span>{{ buttonText }}</span>
      </AppButton>
    </div>
  </div>
</template>

<style scoped>
.api-key-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.field-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--ink, #f2f4f7);
}
.input-action-wrapper {
  display: flex;
  gap: 8px;
  align-items: center;
}
.input-container {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
}
.key-input {
  width: 100%;
  padding: 8px 36px 8px 12px;
  background: var(--surface, #11141a);
  border: 1px solid var(--line, rgba(255, 255, 255, 0.12));
  border-radius: 8px;
  color: var(--ink, #ffffff);
  font-size: 13px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}
.key-input:focus {
  border-color: var(--color-border-strong);
}
.toggle-visibility-btn {
  position: absolute;
  right: 8px;
  background: transparent;
  border: none;
  color: var(--muted, #9aa4b2);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
}
.toggle-visibility-btn:hover {
  color: var(--ink, #ffffff);
}
.save-key-btn {
  white-space: nowrap;
}
</style>
