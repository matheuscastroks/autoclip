<script setup lang="ts">
import AppButton from '../AppButton.vue';
import AppIcon from '../ui/AppIcon.vue';
import { time } from '../../format';
defineProps<{ count: number; durationUs: number; disabled: boolean; conflict: boolean }>();
defineEmits<{ generate: [] }>();
</script>
<template>
  <footer class="selection-dock">
    <div>
      <strong
        >{{ count }} proposta{{ count === 1 ? '' : 's' }} selecionada{{
          count === 1 ? '' : 's'
        }}</strong
      >
      <p v-if="conflict" role="status">Revise propostas inválidas ou sobrepostas antes de gerar.</p>
      <p v-else>
        {{
          count
            ? 'Duração estimada: ' + time(durationUs)
            : 'Selecione propostas para avaliar o resultado em prévias leves.'
        }}
      </p>
    </div>
    <AppButton
      class="button primary"
      data-action="generate-selected"
      :disabled="disabled"
      @click="$emit('generate')"
      ><AppIcon name="scissors" size="sm" />Gerar prévias rápidas</AppButton
    >
  </footer>
</template>
<style scoped>
.selection-dock {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  flex-shrink: 0;
  border-top: 1px solid var(--color-border-subtle);
  padding-top: 16px;
}
strong {
  font-size: var(--font-size-body);
  font-weight: 600;
}
p {
  color: var(--color-text-secondary);
  font-size: var(--font-size-meta);
  margin-top: 4px;
}
</style>
