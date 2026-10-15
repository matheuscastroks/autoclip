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
import Link from '~icons/fluent/link-24-regular';
import Check from '~icons/fluent/checkmark-24-regular';
import Warning from '~icons/fluent/warning-24-regular';
import Clock from '~icons/fluent/clock-24-regular';
import Key from '~icons/fluent/key-24-regular';
import Eye from '~icons/fluent/eye-24-regular';
import EyeOff from '~icons/fluent/eye-off-24-regular';
import Save from '~icons/fluent/save-24-regular';
import Cpu from '~icons/fluent/developer-board-24-regular';
import Sparkle from '~icons/fluent/sparkle-24-regular';
import CheckCircle from '~icons/fluent/checkmark-circle-24-regular';
import Stop from '~icons/fluent/stop-24-regular';
import OpenExternal from '~icons/fluent/open-24-regular';
import Spinner from '~icons/fluent/spinner-ios-20-regular';
import Download from '~icons/fluent/arrow-download-24-regular';
import Globe from '~icons/fluent/globe-24-regular';
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
  link: { regular: Link, label: 'Link' },
  check: { regular: Check, label: 'Concluído' },
  warning: { regular: Warning, label: 'Atenção' },
  clock: { regular: Clock, label: 'Aguardando' },
  key: { regular: Key, label: 'Credencial' },
  eye: { regular: Eye, label: 'Mostrar' },
  'eye-off': { regular: EyeOff, label: 'Ocultar' },
  save: { regular: Save, label: 'Salvar' },
  cpu: { regular: Cpu, label: 'Processamento local' },
  sparkle: { regular: Sparkle, label: 'Análise' },
  'check-circle': { regular: CheckCircle, label: 'Concluído' },
  stop: { regular: Stop, label: 'Cancelar' },
  'open-external': { regular: OpenExternal, label: 'Abrir' },
  spinner: { regular: Spinner, label: 'Em andamento' },
  download: { regular: Download, label: 'Baixar' },
  globe: { regular: Globe, label: 'Provedor remoto' },
} satisfies Record<string, IconDefinition>;

export type IconName = keyof typeof icons;
export function getIcon(name: IconName): IconDefinition | undefined {
  return Object.hasOwn(icons, name) ? icons[name] : undefined;
}
