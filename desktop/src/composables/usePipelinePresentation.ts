import { computed, toRef } from 'vue';
import type { AnalysisView, Job, Project, Revision } from '../types';
import { active, latestJob, stages } from '../format';
import { PIPELINE_STEPS, usePipelineSteps } from './usePipelineSteps';
import { useRenderFailures } from './useRenderFailures';

export interface PipelineInput {
  project: Project;
  jobs: Job[];
  busy: boolean;
  hasCuts: boolean;
  revisions?: Revision[];
  analysis?: AnalysisView | null;
  selectedCount?: number;
  selectedCandidateIds?: string[];
}
export interface PipelineAction {
  id:
    | 'transcribe'
    | 'analyze'
    | 'analysis'
    | 'review'
    | 'generate'
    | 'export'
    | 'resume'
    | 'replaceSource'
    | 'cancel';
  label: string;
  disabled?: boolean;
  jobId?: string;
}
export interface PipelineHero {
  state: 'ready' | 'processing' | 'attention';
  title: string;
  description: string;
  primary?: PipelineAction;
  secondary?: PipelineAction[];
  notice?: string;
  errorDetails?: boolean;
  progress?: { label: string; value?: number; total?: number };
}

export function usePipelinePresentation(props: Readonly<PipelineInput>) {
  const job = computed(() => latestJob(props.jobs));
  const processing = computed(() => props.jobs.some(j => active(j.status)));
  const recovery = computed(
    () => !!job.value && ['failed', 'cancelled', 'interrupted'].includes(job.value.status)
  );
  const importRecovery = computed(
    () =>
      recovery.value &&
      !props.project.source &&
      ['prepare', 'import'].includes(job.value?.operation || '')
  );
  const { getStepState } = usePipelineSteps({
    project: toRef(props, 'project'),
    job,
    revisions: toRef(props, 'revisions'),
    selectedCount: computed(() => props.selectedCount || 0),
    importRecovery,
    hasCuts: toRef(props, 'hasCuts'),
  });
  const { failedRenderItem, lastFailureReason } = useRenderFailures(
    computed(() => (job.value ? [job.value] : [])),
    importRecovery,
    recovery,
    job
  );
  const validFinal = (r: Revision) =>
    r.technical_pass && (!r.final_state || r.final_state === 'available');
  const approved = computed(() =>
    props.revisions?.some(r => validFinal(r) && r.review_status === 'approved')
  );
  const pendingExport = computed(() =>
    props.revisions?.some(r => validFinal(r) && r.review_status === 'approved' && !r.exported)
  );
  const needsFinalReview = computed(() =>
    props.revisions?.some(
      r => validFinal(r) && ['needs_review', 'stale_review'].includes(r.review_status)
    )
  );
  const hasPreviews = computed(() =>
    props.revisions?.some(r => r.preview?.state === 'available' && !validFinal(r))
  );
  const pendingSelectedCount = computed(() =>
    props.selectedCandidateIds
      ? props.selectedCandidateIds.filter(
          id =>
            !props.revisions?.some(
              r => r.candidate_id === id && (r.preview?.state === 'available' || validFinal(r))
            )
        ).length
      : props.hasCuts
        ? 0
        : props.selectedCount || 0
  );
  const canGenerate = computed(
    () =>
      !props.busy &&
      !processing.value &&
      !props.project.is_manual &&
      !!props.selectedCount &&
      props.analysis?.state === 'completed'
  );
  const action = (
    id: PipelineAction['id'],
    label: string,
    disabled = false,
    jobId?: string
  ): PipelineAction => ({ id, label, disabled, jobId });
  const technicalSteps = computed(() =>
    PIPELINE_STEPS.map(([id, title]) => {
      const actions: PipelineAction[] = [];
      if (!props.project.is_manual) {
        if (id === 'transcribe' && !props.project.has_transcript && !processing.value)
          actions.push(
            action('transcribe', 'Transcrever vídeo', props.busy || !props.project.source)
          );
        if (id === 'analyze' && props.project.has_transcript && !processing.value)
          actions.push(
            action(
              'analyze',
              props.project.has_analysis ? 'Nova análise' : 'Iniciar análise',
              props.busy
            )
          );
        if (id === 'choose')
          actions.push(
            action('analysis', 'Escolher trechos', props.busy || !props.project.has_analysis)
          );
        if (id === 'render')
          actions.push(action('generate', 'Gerar prévias rápidas', !canGenerate.value));
        if (id === 'export' && approved.value)
          actions.push(action('export', 'Exportar aprovados', props.busy || processing.value));
      }
      return { id, title, state: getStepState(id), actions };
    })
  );
  const overviewSteps = computed(() =>
    technicalSteps.value
      .filter(s => ['import', 'transcribe', 'analyze'].includes(s.id))
      .map(s => ({
        ...s,
        title: {
          import: 'Vídeo importado',
          transcribe: 'Transcrição',
          analyze: 'Análise editorial',
        }[s.id as 'import' | 'transcribe' | 'analyze'],
        actions: [],
      }))
  );

  const hero = computed<PipelineHero>(() => {
    const current = job.value;
    const review = action('review', 'Abrir cortes');
    if (processing.value && current) {
      const final = current.operation === 'render_final';
      const preview = current.operation === 'preview';
      const stage =
        current.progress?.phase || current.stage || current.progress?.stage || current.operation;
      const title =
        current.status === 'cancelling'
          ? 'Cancelando tarefa'
          : current.status === 'pending'
            ? final
              ? 'Versão final na fila'
              : preview
                ? 'Prévias na fila'
                : 'Processamento na fila'
            : final
              ? stage === 'verify'
                ? 'Validando versão final'
                : 'Renderizando versão final'
              : preview
                ? 'Gerando prévias rápidas'
                : stages[stage] ||
                  (current.operation === 'prepare'
                    ? 'Preparando vídeo'
                    : 'Processamento em andamento');
      const progress = current.progress;
      const counts =
        progress &&
        typeof progress.total_items === 'number' &&
        progress.total_items > 0 &&
        typeof progress.completed_items === 'number' &&
        progress.completed_items >= 0 &&
        progress.completed_items <= progress.total_items;
      return {
        state: 'processing',
        title,
        description:
          current.status === 'pending'
            ? current.queue_reason || 'Aguardando o motor local. Você pode continuar navegando.'
            : 'O trabalho continua em segundo plano. Você pode navegar sem interrompê-lo.',
        primary: action(
          'cancel',
          current.status === 'pending'
            ? 'Remover da fila'
            : current.status === 'cancelling'
              ? 'Cancelando…'
              : 'Cancelar',
          props.busy || current.status === 'cancelling',
          current.id
        ),
        progress:
          current.status === 'pending'
            ? undefined
            : counts
              ? {
                  label: `${progress.completed_items} de ${progress.total_items} cortes processados`,
                  value: progress.completed_items!,
                  total: progress.total_items!,
                }
              : { label: title },
      };
    }
    if (
      recovery.value ||
      failedRenderItem.value ||
      (!current && props.project.status === 'failed')
    ) {
      const title = importRecovery.value
        ? 'Falha na importação do vídeo'
        : current?.status === 'interrupted'
          ? 'Tarefa interrompida'
          : current?.status === 'cancelled'
            ? 'Tarefa cancelada'
            : 'O processamento precisa de atenção';
      return {
        state: 'attention',
        title,
        description:
          'Os resultados preservados continuam disponíveis. Retome quando estiver pronto.',
        notice:
          current?.error?.message ||
          failedRenderItem.value?.item.error_message ||
          props.project.error?.message ||
          lastFailureReason.value,
        errorDetails: true,
        primary: current
          ? action(
              'resume',
              importRecovery.value ? 'Tentar novamente' : 'Retomar processamento',
              props.busy,
              current.id
            )
          : undefined,
        secondary:
          importRecovery.value && current
            ? [action('replaceSource', 'Usar arquivo local', props.busy, current.id)]
            : props.hasCuts
              ? [review]
              : props.project.has_analysis
                ? [action('analysis', 'Consultar análise')]
                : [],
      };
    }
    if (props.project.is_manual)
      return {
        state: 'ready',
        title: 'Prévia técnica manual',
        description:
          'Consulte o teste em Cortes. Uma prévia técnica não equivale à aprovação editorial.',
        primary: review,
      };
    if (!props.project.has_transcript && !props.hasCuts)
      return {
        state: 'ready',
        title: props.project.source ? 'Transcrição pendente' : 'Vídeo ainda não importado',
        description: props.project.source
          ? 'Gere a transcrição com marcação temporal para consultar o vídeo e iniciar a análise.'
          : 'A fonte ainda não está disponível. Consulte a fila de tarefas para acompanhar a importação.',
        primary: action('transcribe', 'Transcrever áudio', props.busy || !props.project.source),
      };
    if (!props.project.has_analysis && !props.hasCuts)
      return {
        state: 'ready',
        title: 'Análise pendente',
        description: 'Analise a transcrição para identificar propostas de cortes.',
        primary: action('analyze', 'Iniciar análise', props.busy),
      };
    if (pendingSelectedCount.value > 0)
      return {
        state: 'ready',
        title: `${pendingSelectedCount.value} proposta(s) aguardando prévia`,
        description:
          'Gere prévias leves com o enquadramento e as legendas. A versão final será solicitada em Cortes.',
        notice:
          props.analysis?.state !== 'completed'
            ? 'Conclua ou recupere a análise antes de gerar prévias.'
            : undefined,
        primary: action('generate', 'Gerar prévias rápidas', !canGenerate.value),
        secondary: [action('analysis', 'Ajustar seleção')],
      };
    if (!props.hasCuts)
      return {
        state: 'ready',
        title: 'Curadoria de cortes disponível',
        description: props.analysis
          ? `${props.analysis.proposals.length} propostas disponíveis para consultar na Análise.`
          : 'Abra a Análise para consultar as propostas disponíveis.',
        primary: action('analysis', 'Selecionar cortes', props.busy),
      };
    if (needsFinalReview.value)
      return {
        state: 'ready',
        title: 'Versões finais para revisar',
        description: 'Confira o vídeo final e os cinco critérios editoriais antes de aprovar.',
        primary: action('review', 'Revisar versões finais'),
        secondary: pendingExport.value ? [action('export', 'Exportar aprovados', props.busy)] : [],
      };
    if (approved.value && !pendingExport.value)
      return {
        state: 'ready',
        title: 'Exportação concluída',
        description:
          'As versões finais aprovadas já foram exportadas. Abra Cortes para consultar os resultados.',
        primary: review,
      };
    if (approved.value)
      return {
        state: 'ready',
        title: 'Cortes aprovados para exportar',
        description: 'A exportação inclui somente versões finais tecnicamente válidas e aprovadas.',
        primary: action('export', 'Exportar aprovados', props.busy),
        secondary: [review],
      };
    if (hasPreviews.value)
      return {
        state: 'ready',
        title: 'Prévias prontas para avaliar',
        description:
          'Avalie as prévias em Cortes. Solicite a versão final apenas dos resultados que quiser publicar.',
        primary: action('review', 'Avaliar prévias'),
      };
    return {
      state: 'ready',
      title: 'Acompanhe seus cortes',
      description: 'Abra Cortes para verificar versões, avisos e ações disponíveis.',
      primary: review,
    };
  });
  return { job, hero, overviewSteps, technicalSteps, lastFailureReason };
}
