import { ref, computed, type Ref } from 'vue';
import type { Proposal } from '../types';
import { overlaps } from '../utils/intervals';

export function useProposalSelection(
  proposalsRef: Ref<Proposal[]>,
  discardedRef: Ref<string[]>
) {
  const selected = ref<string[]>([]);

  const validSelection = computed(() => {
    const list: string[] = [];
    const validProposals = proposalsRef.value.filter(
      p => !discardedRef.value.includes(p.candidate_id)
    );

    for (const id of selected.value) {
      const target = validProposals.find(p => p.candidate_id === id);
      if (!target) continue;

      const hasOverlap = list.some(keptId => {
        const kept = validProposals.find(p => p.candidate_id === keptId);
        if (!kept) return false;
        return overlaps(
          { start: target.start_us, end: target.end_us },
          { start: kept.start_us, end: kept.end_us }
        );
      });

      if (!hasOverlap) {
        list.push(id);
      }
    }

    return list;
  });

  function hasOverlapWithSelected(proposal: Proposal): boolean {
    return validSelection.value.some(id => {
      if (id === proposal.candidate_id) return false;
      const kept = proposalsRef.value.find(p => p.candidate_id === id);
      if (!kept) return false;
      return overlaps(
        { start: proposal.start_us, end: proposal.end_us },
        { start: kept.start_us, end: kept.end_us }
      );
    });
  }

  function toggle(id: string) {
    if (selected.value.includes(id)) {
      selected.value = selected.value.filter(s => s !== id);
    } else {
      const target = proposalsRef.value.find(p => p.candidate_id === id);
      if (target && hasOverlapWithSelected(target)) {
        return false;
      }
      selected.value = [...selected.value, id];
    }
    return true;
  }

  function selectAllEligible(topicFilter = '') {
    const toSelect: string[] = [];
    const candidates = proposalsRef.value.filter(
      p =>
        p.eligible &&
        !discardedRef.value.includes(p.candidate_id) &&
        (!topicFilter || p.group_id === topicFilter)
    );

    for (const c of candidates) {
      const hasConflict = toSelect.some(id => {
        const kept = proposalsRef.value.find(p => p.candidate_id === id);
        if (!kept) return false;
        return overlaps(
          { start: c.start_us, end: c.end_us },
          { start: kept.start_us, end: kept.end_us }
        );
      });

      if (!hasConflict) {
        toSelect.push(c.candidate_id);
      }
    }

    selected.value = toSelect;
    return toSelect;
  }

  function clearSelection() {
    selected.value = [];
  }

  function setSelection(ids: string[]) {
    selected.value = ids;
  }

  return {
    selected,
    validSelection,
    hasOverlapWithSelected,
    toggle,
    selectAllEligible,
    clearSelection,
    setSelection,
  };
}
