import type { Job, Project, AnalysisView } from './types';
export const analysisLabels: Record<AnalysisView['state'], string> = {
  not_started: 'Análise ainda não iniciada',
  running: 'Analisando a transcrição',
  partial: 'Análise parcial disponível',
  completed: 'Análise concluída',
  failed: 'Análise precisa de atenção',
  cancelled: 'Análise cancelada',
  interrupted: 'Análise interrompida',
  invalid: 'Análise salva inválida',
  unavailable: 'Análise salva indisponível',
  stale: 'Análise salva desatualizada',
};
export function projectLabel(status: Project['status']) {
  // The project records the pipeline stage; editorial decisions belong to each revision.
  return status === 'needs_review' ? 'Cortes gerados' : labels[status] || status;
}
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
export function time(us: number | null | undefined = 0) {
  const s = Math.floor((us ?? 0) / 1e6);
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
  initializing: 'Iniciando tarefa',
  model_load: 'Carregando modelo local',
  integrity: 'Verificando integridade',
  download: 'Baixando arquivos',
  copy: 'Copiando arquivos',
  ffmpeg: 'Baixando ferramentas',
  whisper: 'Baixando modelo local',
  extracting_ffmpeg: 'Extraindo ferramentas',
  starting: 'Iniciando instalação',
  done: 'Concluído',
  import: 'Importando vídeo',
  audio: 'Preparando áudio',
  transcribe: 'Transcrevendo',
  analyze: 'Analisando temas',
  select: 'Selecionando trechos',
  edit_plan: 'Preparando edição',
  reframe: 'Acompanhando rosto',
  captions: 'Gerando legendas',
  render: 'Renderizando',
  preview: 'Gerando prévias rápidas',
  render_final: 'Renderizando versão final',
  verify: 'Validando saída',
  export: 'Exportando',
};
