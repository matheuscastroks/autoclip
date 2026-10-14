<script setup lang="ts">
import { toRef } from 'vue';
import AppButton from './AppButton.vue';
import type { Job } from '../types';
import { labels, stages } from '../format';
import { useJobQueue } from '../composables/useJobQueue';

const props = defineProps<{ jobs: Job[]; busy: boolean }>();
defineEmits<{ cancel: [id: string] }>();

const { activeJobs: queue, runningCount, pendingCount } = useJobQueue(toRef(props, 'jobs'));
</script>
<template>
  <section v-if="queue.length" class="project-queue" aria-label="Fila deste projeto">
    <header>
      <strong>Fila do projeto</strong>
      <span>{{ runningCount }} em execução · {{ pendingCount }} aguardando</span>
    </header>
    <ol>
      <li v-for="job in queue" :key="job.id">
        <div>
          <strong>{{ stages[job.stage || job.operation] || job.operation }}</strong>
          <span>
            <el-tag
              size="small"
              :type="job.status === 'running' ? 'primary' : 'info'"
              effect="dark"
              style="margin-right: 4px"
            >
              {{ labels[job.status] }}
            </el-tag>
            <template v-if="job.status === 'pending'">
              · posição {{ job.queue_position || '—' }}</template
            >
          </span>
          <small v-if="job.status === 'pending'">{{
            job.queue_reason || 'Aguardando despacho.'
          }}</small>
          <small v-else-if="job.progress?.total_items"
            >{{ job.progress.completed_items || 0 }}/{{ job.progress.total_items }} prévias
            prontas</small
          >
        </div>
        <AppButton
          class="button small secondary"
          :disabled="busy || job.status === 'cancelling'"
          @click="$emit('cancel', job.id)"
          >{{ job.status === 'pending' ? 'Remover da fila' : 'Cancelar' }}</AppButton
        >
      </li>
    </ol>
  </section>
</template>
<style scoped>
.project-queue {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 16px;
}
.project-queue header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}
.project-queue header span,
.project-queue small {
  color: var(--muted);
}
ol {
  list-style: none;
  padding: 0;
  margin: 8px 0 0;
}
li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 8px 0;
  border-top: 1px solid var(--line);
}
li div {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 14px;
  align-items: center;
}
li small {
  flex-basis: 100%;
}
</style>
