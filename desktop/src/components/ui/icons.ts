import Folder from '~icons/fluent/folder-24-regular';
import FolderFilled from '~icons/fluent/folder-24-filled';
import Settings from '~icons/fluent/settings-24-regular';
import SettingsFilled from '~icons/fluent/settings-24-filled';
import Queue from '~icons/fluent/task-list-ltr-24-regular';
import QueueFilled from '~icons/fluent/task-list-ltr-24-filled';
import Add from '~icons/fluent/add-24-regular';
import FolderOpen from '~icons/fluent/folder-open-24-regular';
import Search from '~icons/fluent/search-24-regular';
import Grid from '~icons/fluent/grid-24-regular';
import List from '~icons/fluent/text-bullet-list-ltr-24-regular';
import Video from '~icons/fluent/video-24-regular';
import Play from '~icons/fluent/play-24-regular';
import Pause from '~icons/fluent/pause-24-regular';
import Close from '~icons/fluent/dismiss-24-regular';
import Trash from '~icons/fluent/delete-24-regular';
import Refresh from '~icons/fluent/arrow-clockwise-24-regular';
import Engine from '~icons/fluent/hard-drive-24-regular';
import Scissors from '~icons/fluent/cut-24-regular';
import Back from '~icons/fluent/arrow-left-24-regular';
import Transcript from '~icons/fluent/document-text-24-regular';
import type { Component } from 'vue';

interface IconDefinition {
  regular: Component;
  filled?: Component;
  label: string;
}

// Build-time allowlist: no runtime provider, arbitrary SVG or dynamic import path.
export const icons = {
  projects: { regular: Folder, filled: FolderFilled, label: 'Projetos' },
  settings: { regular: Settings, filled: SettingsFilled, label: 'Configurações' },
  queue: { regular: Queue, filled: QueueFilled, label: 'Fila de tarefas' },
  add: { regular: Add, label: 'Adicionar' },
  'folder-open': { regular: FolderOpen, label: 'Abrir pasta' },
  search: { regular: Search, label: 'Buscar' },
  grid: { regular: Grid, label: 'Grade' },
  list: { regular: List, label: 'Lista' },
  video: { regular: Video, label: 'Vídeo' },
  play: { regular: Play, label: 'Reproduzir' },
  pause: { regular: Pause, label: 'Pausar' },
  close: { regular: Close, label: 'Fechar' },
  trash: { regular: Trash, label: 'Mover para a lixeira' },
  refresh: { regular: Refresh, label: 'Atualizar' },
  engine: { regular: Engine, label: 'Motor local' },
  scissors: { regular: Scissors, label: 'Cortes' },
  back: { regular: Back, label: 'Voltar' },
  transcript: { regular: Transcript, label: 'Transcrição' },
} satisfies Record<string, IconDefinition>;

export type IconName = keyof typeof icons;
export function getIcon(name: IconName): IconDefinition | undefined {
  return Object.hasOwn(icons, name) ? icons[name] : undefined;
}
