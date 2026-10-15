<script setup lang="ts">
import type { Proposal } from '../../types';
import { time } from '../../format';
import AppIcon from '../ui/AppIcon.vue';
defineProps<{
  proposal: Proposal;
  selected: boolean;
  discarded: boolean;
  overlapping: boolean;
  focused: boolean;
  busy: boolean;
  analysisComplete: boolean;
}>();
defineEmits<{ inspect: []; toggle: []; discard: []; restore: [] }>();
</script>
<template>
  <article class="proposal-item" :class="{ checked: selected, focused, discarded, overlapping }">
    <div class="proposal-item-heading">
      <input
        type="checkbox"
        :aria-label="'Selecionar ' + proposal.title"
        :checked="selected"
        :disabled="
          busy || !analysisComplete || !proposal.eligible || discarded || (!selected && overlapping)
        "
        @change="$emit('toggle')"
      />
      <button type="button" class="proposal-open" @click="$emit('inspect')">
        <strong>{{ proposal.title }}</strong
        ><span
          >{{ time(proposal.start_us) }} – {{ time(proposal.end_us) }} ·
          {{ time(proposal.duration_us) }}</span
        >
      </button>
      <button
        type="button"
        :disabled="busy"
        :data-action="discarded ? 'restore-proposal' : 'discard-proposal'"
        :aria-label="(discarded ? 'Restaurar ' : 'Descartar ') + proposal.title"
        @click="discarded ? $emit('restore') : $emit('discard')"
      >
        <AppIcon :name="discarded ? 'refresh' : 'trash'" size="sm" />
      </button>
    </div>
    <p class="proposal-summary">{{ proposal.rationale }}</p>
    <div class="proposal-item-footer">
      <span v-if="discarded">Descartada</span>
      <span v-else-if="overlapping" class="proposal-warning">Sobrepõe seleção</span>
      <span v-else-if="!proposal.eligible" class="proposal-warning"
        >Não elegível · {{ proposal.reasons.join(' ') }}</span
      >
      <span v-else>Elegível</span>
      <button type="button" class="text-button" @click="$emit('inspect')">Examinar contexto</button>
    </div>
  </article>
</template>
<style scoped>
.proposal-item {
  padding: 16px 0;
  border-bottom: 1px solid var(--color-border-subtle);
  min-width: 0;
}
.proposal-item.checked {
  border-left: 3px solid var(--color-action-primary);
  padding-left: 12px;
}
.proposal-item-heading {
  display: flex;
  align-items: start;
  gap: 12px;
}
.proposal-item-heading > input {
  margin-top: 6px;
  flex-shrink: 0;
}
.proposal-item-heading > button:last-child {
  padding: 6px;
  flex-shrink: 0;
  background: transparent;
  color: var(--color-text-secondary);
  border: 0;
}
.proposal-open {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  padding: 0;
  border: 0;
  background: transparent;
  text-align: left;
}
.proposal-open strong {
  font-size: var(--font-size-body);
  font-weight: 600;
  overflow-wrap: anywhere;
}
.proposal-open span,
.proposal-item-footer {
  font-size: var(--font-size-meta);
  color: var(--color-text-secondary);
}
.proposal-summary {
  margin: 8px 0 8px 28px;
  font-size: var(--font-size-control);
  max-width: 75ch;
  color: var(--color-text-secondary);
}
.proposal-item-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
  margin-left: 28px;
}
.proposal-warning {
  color: var(--color-warning-text);
}
</style>
