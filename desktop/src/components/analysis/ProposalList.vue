<script setup lang="ts">
import type { Proposal } from '../../types';
import ProposalItem from './ProposalItem.vue';
defineProps<{
  proposals: Proposal[];
  selectedIds: string[];
  discardedIds: string[];
  overlappingIds: string[];
  focusedId: string;
  busy: boolean;
  analysisComplete: boolean;
  counts: { active: number; discarded: number; all: number };
}>();
const search = defineModel<string>('search', { default: '' });
const filterMode = defineModel<'active' | 'discarded' | 'all'>('filterMode', { default: 'active' });
defineEmits<{
  focusProposal: [id: string];
  toggleSelection: [proposal: Proposal];
  discardProposal: [id: string];
  restoreProposal: [id: string];
  selectEligible: [];
  clearSelection: [];
}>();
</script>
<template>
  <section class="proposal-region" aria-label="Lista de propostas de cortes">
    <header class="proposal-list-heading">
      <h3>
        Propostas <small>{{ proposals.length }}</small>
      </h3>
      <div class="bulk-actions">
        <button
          type="button"
          data-action="select-all-proposals"
          :disabled="busy || !analysisComplete || !counts.active"
          @click="$emit('selectEligible')"
        >
          Selecionar elegíveis</button
        ><button
          type="button"
          data-action="clear-selection"
          :disabled="busy || !selectedIds.length"
          @click="$emit('clearSelection')"
        >
          Limpar seleção
        </button>
      </div>
    </header>
    <div class="proposal-list-toolbar">
      <input
        v-model="search"
        type="search"
        placeholder="Buscar na fala ou justificativa"
        aria-label="Buscar nas propostas"
      />
      <div class="proposal-filters" aria-label="Filtro de propostas">
        <button
          v-for="mode in ['active', 'discarded', 'all'] as const"
          :key="mode"
          type="button"
          class="filter-pill-btn"
          :aria-pressed="filterMode === mode"
          @click="filterMode = mode"
        >
          {{ { active: 'Ativas', discarded: 'Descartadas', all: 'Todas' }[mode] }} ({{
            counts[mode]
          }})
        </button>
      </div>
    </div>
    <div class="proposal-items" tabindex="0" role="region" aria-label="Propostas de cortes">
      <ProposalItem
        v-for="proposal in proposals"
        :key="proposal.candidate_id"
        :proposal="proposal"
        :selected="selectedIds.includes(proposal.candidate_id)"
        :discarded="discardedIds.includes(proposal.candidate_id)"
        :overlapping="overlappingIds.includes(proposal.candidate_id)"
        :focused="focusedId === proposal.candidate_id"
        :busy="busy"
        :analysis-complete="analysisComplete"
        @inspect="$emit('focusProposal', proposal.candidate_id)"
        @toggle="$emit('toggleSelection', proposal)"
        @discard="$emit('discardProposal', proposal.candidate_id)"
        @restore="$emit('restoreProposal', proposal.candidate_id)"
      />
      <div v-if="!proposals.length" class="proposal-empty">
        <h3>
          {{ counts.all ? 'Nenhuma proposta corresponde ao filtro' : 'Os trechos aparecerão aqui' }}
        </h3>
        <p>
          {{
            counts.all
              ? 'Ajuste a busca, o tema ou o filtro de propostas.'
              : 'Consulte a Preparação para iniciar ou recuperar a análise. Propostas validadas aparecerão nesta lista.'
          }}
        </p>
      </div>
    </div>
  </section>
</template>
<style scoped>
.proposal-region {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  gap: 16px;
}
.proposal-list-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
h3 {
  font-size: var(--font-size-region);
  font-weight: 600;
}
small {
  color: var(--color-text-secondary);
  font-size: var(--font-size-meta);
  margin-left: 8px;
}
.bulk-actions,
.proposal-filters {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.bulk-actions button,
.proposal-filters button {
  background: transparent;
  border: 1px solid var(--color-border-subtle);
  border-radius: 6px;
  padding: 6px 8px;
  color: var(--color-text-secondary);
  font-size: var(--font-size-control);
}
.proposal-filters button[aria-pressed='true'] {
  background: var(--color-surface-selected);
  color: var(--color-text-primary);
}
.proposal-list-toolbar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.proposal-list-toolbar input {
  flex: 1;
  min-width: 180px;
  padding: 6px 10px;
  color: var(--color-text-primary);
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
  border-radius: 6px;
}
.proposal-items {
  overflow: auto;
  min-height: 0;
  flex: 1;
  padding-right: 8px;
}
.proposal-empty {
  display: block;
  padding: 24px 0;
  min-height: 0;
  text-align: left;
}
.proposal-empty p {
  margin-top: 8px;
  max-width: 65ch;
}
</style>
