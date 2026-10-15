import type { Job } from './types';
export const active = (status: string) => ['pending', 'running', 'cancelling'].includes(status);
export function latestJob(jobs: Job[]) {
  const ordered = [...jobs].sort(
    (a, b) => b.created_at.localeCompare(a.created_at) || b.id.localeCompare(a.id)
  );
  return (
    ordered.find(j => ['running', 'cancelling'].includes(j.status)) ||
    ordered.find(j => j.status === 'pending') ||
    ordered[0]
  );
}
export function time(us = 0) {
  const s = Math.floor(us / 1e6);
  const hours = Math.floor(s / 3600);
  const minutes = Math.floor((s % 3600) / 60);
  const seconds = s % 60;

  if (hours > 0) {
    return `${hours.toString().padStart(2, '0')}:${minutes
      .toString()
      .padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  }

  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}
export const labels: Record<string, string> = {
  ready: 'Pronto',
  pending_import: 'Aguardando importação',
  imported: 'Pronto para transcrever',
  transcribed: 'Transcrito',
  analyzed: 'Analisado',
  processing: 'Processando',
  needs_review: 'Revisão editorial pendente',
  no_candidates: 'Sem cortes elegíveis',
  completed: 'Concluído',
  failed: 'Precisa de atenção',
  cancelled: 'Cancelado',
  interrupted: 'Interrompido',
  manual_preview: 'Prévia manual',
  pending: 'Na fila',
  running: 'Em execução',
  cancelling: 'Cancelando',
  approved: 'Aprovado',
  rejected: 'Rejeitado',
  stale_review: 'Revisar novamente',
  invalid: 'Indisponível',
};
export const stages: Record<string, string> = {
  import: 'Importando vídeo',
  audio: 'Preparando áudio',
  transcribe: 'Transcrevendo',
  analyze: 'Analisando temas',
  select: 'Selecionando trechos',
  edit_plan: 'Preparando edição',
  reframe: 'Acompanhando rosto',
  captions: 'Gerando legendas',
  render: 'Renderizando',
  verify: 'Verificando prévia',
  export: 'Exportando',
};
