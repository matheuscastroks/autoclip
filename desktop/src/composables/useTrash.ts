import { ref } from 'vue';
import { api } from '../api';

export interface TrashItem {
  id: string;
  name: string;
}

export function useTrash() {
  const trashRows = ref<TrashItem[]>([]);
  const trashKind = ref<'projects' | 'cuts'>('projects');
  const trashDialog = ref<HTMLDialogElement>();

  async function openTrash(kind: 'projects' | 'cuts', currentProjectId?: string) {
    trashKind.value = kind;
    if (kind === 'projects') {
      const items = await api.trash();
      trashRows.value = items.map(item => ({ id: item.id, name: item.name }));
    } else if (currentProjectId) {
      const items = await api.deletedClips(currentProjectId);
      trashRows.value = items.map(r => ({ id: r.revision_id, name: r.title }));
    } else {
      trashRows.value = [];
    }
    trashDialog.value?.showModal();
  }

  async function restoreItem(id: string, currentProjectId?: string) {
    if (trashKind.value === 'projects') {
      await api.restoreProject(id);
    } else if (currentProjectId) {
      await api.restoreClip(currentProjectId, id);
    }
    trashRows.value = trashRows.value.filter(r => r.id !== id);
  }

  function closeTrash() {
    trashDialog.value?.close();
  }

  return {
    trashRows,
    trashKind,
    trashDialog,
    openTrash,
    restoreItem,
    closeTrash,
  };
}
