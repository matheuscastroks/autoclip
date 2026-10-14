<script setup lang="ts">
import AppButton from './AppButton.vue';
import { computed, ref, onMounted, onUnmounted } from 'vue';
import type { Job, Revision, GenerationItem } from '../types';
import { latestJob, active } from '../format';
const props = defineProps<{ jobs: Job[]; revisions?: Revision[] }>();
defineEmits<{
  resume: [id: string];
  select: [id: string];
  retry: [value: { job_id: string; candidate_id: string }];
}>();
const job = computed(() => latestJob(props.jobs.filter(j => j.operation === 'render')));
const statePriority: Record<string, number> = { running: 0, failed: 1, waiting: 2, ready: 3 };
const orderedItems = computed(() => {
  const seen = new Set<string>();
  const items: (GenerationItem & { retry_job_id: string })[] = [];
  for (const row of [...props.jobs]
    .filter(j => j.operation === 'render')
    .sort((a, b) => b.created_at.localeCompare(a.created_at) || b.id.localeCompare(a.id))) {
    for (const item of row.progress?.items || []) {
      if (seen.has(item.candidate_id)) continue;
      seen.add(item.candidate_id);
      if (!['ready', 'cancelled'].includes(item.state))
        items.push({ ...item, retry_job_id: row.id });
    }
  }
  return items.sort((a, b) => (statePriority[a.state] ?? 2) - (statePriority[b.state] ?? 2));
});
const now = ref(Date.now());
let timer: ReturnType<typeof setInterval> | undefined;
onMounted(() => {
  timer = setInterval(() => (now.value = Date.now()), 1000);
});
onUnmounted(() => {
  if (timer) clearInterval(timer);
});
const elapsed = computed(() => {
  const start = Date.parse(job.value?.created_at || '');
  if (!Number.isFinite(start)) return '';
  const seconds = Math.max(0, Math.floor((now.value - start) / 1000));
  return `${Math.floor(seconds / 60)} min ${String(seconds % 60).padStart(2, '0')} s`;
});
const phases: Record<string, string> = {
  waiting: 'Na fila',
  edit_plan: 'Preparando edição',
  pauses: 'Verificando pausas',
  reframe: 'Acompanhando rosto',
  captions: 'Sincronizando legendas',
  render: 'Codificando vídeo',
  verify: 'Verificando áudio e vídeo',
  ready: 'Pronta para revisar',
  failed: 'Falha neste corte',
};
</script>
<template>
  <section v-if="orderedItems.length" class="generation-queue">
    <header>
      <h3>Geração de prévias</h3>
      <span>{{ orderedItems.length }} pendente(s)</span>
    </header>
    <p v-if="job?.progress?.phase === 'pauses'" class="subtle">
      Verificando pausas no áudio antes de gerar as prévias
    </p>
    <p v-if="elapsed && job && active(job.status)" class="subtle">
      Em andamento há {{ elapsed }} · Sem estimativa de conclusão
    </p>
    <ol>
      <li v-for="item in orderedItems" :key="item.candidate_id" :data-state="item.state">
        <div>
          <strong>{{ item.title || 'Trecho selecionado' }}</strong
          ><span
            >{{
              item.state === 'running' && !active(job?.status || '')
                ? 'Interrompida'
                : phases[item.phase] || item.phase
            }}{{ item.reused && item.state === 'ready' ? ' · reaproveitada' : '' }}</span
          >
        </div>
        <div
          v-if="['render', 'reframe'].includes(item.phase) && item.total_us"
          class="queue-progress"
          role="progressbar"
          :aria-label="
            (item.phase === 'reframe' ? 'Acompanhamento facial de ' : 'Codificação de ') +
            (item.title || 'trecho')
          "
          :aria-valuenow="Math.min(100, Math.floor((item.processed_us / item.total_us) * 100))"
          aria-valuemin="0"
          aria-valuemax="100"
        >
          <span
            :style="{ width: Math.min(100, (item.processed_us / item.total_us) * 100) + '%' }"
          ></span>
        </div>
        <small v-if="['render', 'reframe'].includes(item.phase) && item.total_us"
          >{{ Math.min(100, Math.floor((item.processed_us / item.total_us) * 100)) }}%
          {{
            item.phase === 'reframe'
              ? 'analisado · Codificação a seguir'
              : 'codificado · Verificação técnica a seguir'
          }}</small
        >
        <div v-if="item.error_code" class="queue-error">
          <p>
            <strong>{{
              item.error_stage ? phases[item.error_stage] || item.error_stage : 'Geração da prévia'
            }}</strong>
            · {{ item.error_code }}
          </p>
          <p>
            {{
              item.error_message ||
              'Esta tentativa antiga não registrou detalhes na fila. Consulte o log do corte na pasta do projeto.'
            }}
          </p>
          <small>As outras prévias foram preservadas. Retome somente as pendentes.</small>
          <details v-if="item.error_type">
            <summary>Detalhes técnicos</summary>
            <small>{{ item.error_type }} · {{ item.error_stage }}</small>
          </details>
        </div>
        <AppButton
          v-if="item.state === 'failed'"
          type="button"
          class="button small secondary"
          :disabled="false"
          :aria-label="'Tentar novamente: ' + item.title"
          @click="$emit('retry', { job_id: item.retry_job_id, candidate_id: item.candidate_id })"
          >Tentar novamente</AppButton
        ><AppButton
          v-if="item.state === 'ready' && item.revision_id"
          type="button"
          class="button small secondary"
          @click="$emit('select', item.revision_id)"
          >Ver prévia</AppButton
        >
      </li>
    </ol>
    <AppButton
      v-if="job && ['failed', 'cancelled', 'interrupted'].includes(job.status)"
      class="button small secondary"
      @click="$emit('resume', job.id)"
      >Continuar prévias pendentes</AppButton
    >
  </section>
  <section v-else-if="job && active(job.status)" class="generation-queue queue-empty">
    <h3>Geração de prévias</h3>
    <p class="subtle">Preparando a fila de renderização…</p>
  </section>
</template>
