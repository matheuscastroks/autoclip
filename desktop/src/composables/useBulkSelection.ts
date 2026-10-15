import { ref, computed, watch, type Ref } from 'vue';
import type { Revision } from '../types';

export function useBulkSelection(
  revisionsRef: Ref<Revision[]>,
  visibleRevisionsRef: Ref<Revision[]>
) {
  const bulk = ref<string[]>([]);

  const allVisible = computed(
    () =>
      visibleRevisionsRef.value.length > 0 &&
      visibleRevisionsRef.value.every(r => bulk.value.includes(r.revision_id))
  );

  const exportableBulk = computed(
    () =>
      bulk.value.length > 0 &&
      bulk.value.every(id =>
        revisionsRef.value.some(
          r => r.revision_id === id && r.technical_pass && r.review_status === 'approved'
        )
      )
  );

  watch(
    () => revisionsRef.value,
    rows => {
      bulk.value = bulk.value.filter(id => rows.some(r => r.revision_id === id));
    }
  );

  function toggleAll() {
    const ids = visibleRevisionsRef.value.map(r => r.revision_id);
    bulk.value = allVisible.value
      ? bulk.value.filter(id => !ids.includes(id))
      : [...new Set([...bulk.value, ...ids])];
  }

  function clearBulk() {
    bulk.value = [];
  }

  return {
    bulk,
    allVisible,
    exportableBulk,
    toggleAll,
    clearBulk,
  };
}
