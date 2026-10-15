import { computed, type Ref } from 'vue';
import type { Job } from '../types';

export function useRenderFailures(
  jobsRef: Ref<Job[]>,
  importRecoveryRef: Ref<boolean>,
  recoveryRef: Ref<boolean>,
  currentJobRef: Ref<Job | undefined>
) {
  const renderJobs = computed(() =>
    jobsRef.value.filter(j => ['render', 'preview', 'render_final'].includes(j.operation))
  );

  const failedRenderItem = computed(() => {
    for (const rj of renderJobs.value) {
      for (const item of rj.progress?.items || []) {
        if (item.state === 'failed') {
          return { item, job: rj };
        }
      }
    }
    return null;
  });

  const pendingQueueCount = computed(() => {
    let count = 0;
    for (const rj of renderJobs.value) {
      for (const it of rj.progress?.items || []) {
        if (['waiting', 'queued', 'pending'].includes(it.state)) count++;
      }
      if (rj.status === 'pending') count++;
    }
    return count;
  });

  const hasFailure = computed(() => {
    return (
      importRecoveryRef.value ||
      !!failedRenderItem.value ||
      (recoveryRef.value &&
        !['analyze', 'render', 'preview', 'render_final'].includes(
          currentJobRef.value?.operation || ''
        ))
    );
  });

  const lastFailureTitle = computed(() => {
    if (importRecoveryRef.value) return 'Falha na importação do arquivo original';
    if (failedRenderItem.value?.item.title) return failedRenderItem.value.item.title;
    if (currentJobRef.value?.error?.message) return currentJobRef.value.error.message;
    return 'Falha no processamento';
  });

  const lastFailureReason = computed(() => {
    if (importRecoveryRef.value)
      return currentJobRef.value?.error?.message || 'Fonte bloqueada ou inacessível';
    if (failedRenderItem.value?.item.error_message)
      return failedRenderItem.value.item.error_message;
    if (failedRenderItem.value?.item.error_code) {
      return `${failedRenderItem.value.item.error_code} · Renderizador`;
    }
    if (currentJobRef.value?.error?.code)
      return `${currentJobRef.value.error.code} · Motor de processamento`;
    if (currentJobRef.value?.error?.message) return currentJobRef.value.error.message;
    return 'Ocorreu um erro durante a execução da etapa.';
  });

  return {
    renderJobs,
    failedRenderItem,
    pendingQueueCount,
    hasFailure,
    lastFailureTitle,
    lastFailureReason,
  };
}
