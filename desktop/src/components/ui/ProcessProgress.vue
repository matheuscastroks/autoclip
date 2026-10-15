<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue';
import type { JobProgress } from '../../generated/api';
import { stages } from '../../format';

const props = withDefaults(
  defineProps<{
    progress?: JobProgress | null;
    status?: string;
    startedAt?: string | null;
    finishedAt?: string | null;
  }>(),
  { status: 'running' }
);
const now = ref(Date.now());
let timer: ReturnType<typeof setInterval> | undefined;
watch(
  () => props.status,
  status => {
    if (timer) clearInterval(timer);
    timer = undefined;
    if (['running', 'cancelling'].includes(status)) {
      timer = setInterval(() => (now.value = Date.now()), 1000);
    }
  },
  { immediate: true }
);
onUnmounted(() => {
  if (timer) clearInterval(timer);
});

function percent(value: unknown) {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 100
    ? Math.floor(value)
    : undefined;
}
const stagePercent = computed(() => {
  const p = props.progress;
  if (p && 'stage_percent' in p) return percent(p.stage_percent);
  return p?.total_us && typeof p.processed_us === 'number'
    ? percent(Math.min(100, Math.max(0, (p.processed_us / p.total_us) * 100)))
    : undefined;
});
const overallPercent = computed(() => percent(props.progress?.overall_percent));
const phase = computed(() => {
  const phase = props.progress?.phase || props.progress?.stage || 'initializing';
  return stages[phase] || 'Processando';
});
const elapsed = computed(() => {
  const start = Date.parse(props.startedAt || '');
  if (Number.isFinite(start)) {
    const end = Date.parse(props.finishedAt || '');
    return Math.max(0, (Number.isFinite(end) ? end : now.value) - start) / 1000;
  }
  return props.progress?.elapsed_seconds;
});
function duration(value: number) {
  if (value < 60) return `${Math.ceil(value)} s`;
  if (value < 3600) return `${Math.ceil(value / 60)} min`;
  return `${Math.floor(value / 3600)} h ${Math.ceil((value % 3600) / 60)} min`;
}
const estimate = computed(() => {
  if (!['running', 'cancelling'].includes(props.status)) return '';
  const p = props.progress;
  if (typeof p?.eta_seconds === 'number') return `~${duration(p.eta_seconds)} restante`;
  if (typeof p?.stage_eta_seconds === 'number')
    return `~${duration(p.stage_eta_seconds)} restante nesta etapa`;
  return 'Estimando conclusão';
});
const warning = computed(() => {
  if (!['running', 'cancelling'].includes(props.status)) return '';
  let code = props.progress?.warning;
  if (!code && props.startedAt && !props.progress?.heartbeat_at && (elapsed.value || 0) >= 30)
    code = 'startup_slow';
  const messages: Record<string, string> = {
    startup_slow: 'Inicialização demorando. O motor ainda não confirmou o início da tarefa.',
    heartbeat_missing: 'Sem atualização do processo. A tarefa não foi cancelada automaticamente.',
    no_advance: 'Sem avanço registrado há pelo menos 2 min. O processo ainda está ativo.',
  };
  return messages[code || ''] || '';
});
</script>

<template>
  <div class="process-progress" :data-status="status">
    <div class="progress-heading">
      <span>{{ phase }}</span>
      <span v-if="stagePercent !== undefined">{{ stagePercent }}% da etapa</span>
    </div>
    <progress
      role="progressbar"
      :aria-label="phase"
      :value="stagePercent"
      max="100"
      :aria-valuenow="stagePercent"
      :aria-valuetext="
        stagePercent === undefined ? 'Progresso ainda não mensurável' : `${stagePercent}% da etapa`
      "
    />
    <div class="progress-details">
      <span v-if="progress?.total_items"
        >{{ progress.completed_items || 0 }} de {{ progress.total_items }} cortes processados</span
      >
      <span v-if="overallPercent !== undefined"
        >{{ overallPercent }}% total{{ status === 'completed' ? '' : ' estimado' }}</span
      >
      <span v-if="typeof elapsed === 'number'">{{ duration(elapsed) }} decorridos</span>
      <span v-if="estimate">{{ estimate }}</span>
      <span v-if="progress?.unit === 'bytes' && typeof progress.completed_units === 'number'">
        {{ (progress.completed_units / 1048576).toFixed(1) }} MB<span v-if="progress.total_units">
          / {{ (progress.total_units / 1048576).toFixed(1) }} MB</span
        >
      </span>
    </div>
    <p v-if="warning" class="progress-warning" role="status">{{ warning }}</p>
  </div>
</template>

<style scoped>
.process-progress {
  display: grid;
  gap: 6px;
  width: 100%;
  min-width: 0;
}
.progress-heading,
.progress-details {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 4px 12px;
}
.progress-heading {
  font-size: var(--font-size-control);
}
.progress-details,
.progress-warning {
  color: var(--color-text-secondary);
  font-size: var(--font-size-caption);
}
progress {
  width: 100%;
  height: 6px;
  accent-color: var(--color-action-primary);
}
.progress-warning {
  margin: 0;
}
</style>
