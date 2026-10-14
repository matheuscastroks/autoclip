import { ref } from 'vue';
import { notify } from '../notifications';

export function useDiscardedProposals() {
  const discarded = ref<string[]>([]);

  function loadDiscarded(hash?: string | null) {
    if (!hash || typeof window === 'undefined') {
      discarded.value = [];
      return;
    }
    try {
      const raw = window.localStorage.getItem(`autoclip:discarded:${hash}`);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed) && parsed.every(item => typeof item === 'string')) {
          discarded.value = parsed;
          return;
        }
      }
    } catch {
      // Ignora erro de JSON e fallback para lista vazia
    }
    discarded.value = [];
  }

  function saveDiscarded(hash?: string | null) {
    if (!hash || typeof window === 'undefined') return;
    try {
      window.localStorage.setItem(`autoclip:discarded:${hash}`, JSON.stringify(discarded.value));
    } catch {
      // Quota ou privacidade desabilitada
    }
  }

  function discardItem(id: string, hash?: string | null) {
    if (!discarded.value.includes(id)) {
      discarded.value = [...discarded.value, id];
      saveDiscarded(hash);
    }
    notify.info('Proposta descartada.');
  }

  function restoreItem(id: string, hash?: string | null) {
    discarded.value = discarded.value.filter(s => s !== id);
    saveDiscarded(hash);
    notify.info('Proposta restaurada.');
  }

  function discardMany(ids: string[], hash?: string | null) {
    const set = new Set(discarded.value);
    let changed = false;
    for (const id of ids) {
      if (!set.has(id)) {
        set.add(id);
        changed = true;
      }
    }
    if (changed) {
      discarded.value = Array.from(set);
      saveDiscarded(hash);
    }
    notify.info('Tema descartado.');
  }

  function restoreMany(ids: string[], hash?: string | null) {
    const toRemove = new Set(ids);
    discarded.value = discarded.value.filter(id => !toRemove.has(id));
    saveDiscarded(hash);
    notify.info('Tema restaurado.');
  }

  return {
    discarded,
    loadDiscarded,
    saveDiscarded,
    discardItem,
    restoreItem,
    discardMany,
    restoreMany,
  };
}
