<script setup lang="ts">
import { computed } from 'vue';
import AppButton from './AppButton.vue';
import StatusTag from './StatusTag.vue';
import ProcessProgress from './ui/ProcessProgress.vue';
import type { Job } from '../types';
import { stages } from '../format';

const props = withDefaults(
  defineProps<{
    job: Job;
    busy?: boolean;
    projectName?: string;
  }>(),
  {
    busy: false,
    projectName: '',
  }
);

defineEmits<{
  cancel: [id: string];
  open: [projectId: string];
}>();

const stageLabel = computed(
  () => stages[props.job.stage || props.job.operation] || props.job.operation
);

const cancelLabel = computed(() =>
  props.job.status === 'pending' ? 'Remover da fila' : 'Cancelar tarefa'
);
</script>

<template>
  <li class="job-queue-item" :data-status="job.status">
    <div class="job-meta">
      <div class="job-title-row">
        <strong class="job-operation">{{ stageLabel }}</strong>
        <span v-if="projectName" class="job-project-name">· {{ projectName }}</span>
      </div>

      <div class="job-status-row">
        <StatusTag :status="job.status" size="small" />
        <span v-if="job.status === 'pending'" class="job-queue-pos">
          · posição {{ job.queue_position || '—' }}
        </span>
      </div>

      <small v-if="job.status === 'pending'" class="job-subtle-info">
        {{ job.queue_reason || 'Aguardando despacho.' }}
      </small>
      <small v-else-if="job.progress?.total_items && !['running', 'cancelling'].includes(job.status)" class="job-subtle-info">
        {{ job.progress.completed_items || 0 }}/{{ job.progress.total_items }} prévias prontas
      </small>
      <ProcessProgress
        v-if="['running', 'cancelling'].includes(job.status)"
        :progress="job.progress"
        :status="job.status"
        :started-at="job.started_at"
        :finished-at="job.finished_at"
      />
    </div>

    <div class="job-actions">
      <AppButton
        v-if="['pending', 'running'].includes(job.status)"
        class="button small secondary cancel-job-btn"
        :disabled="busy || job.status === 'cancelling'"
        @click="$emit('cancel', job.id)"
      >
        {{ cancelLabel }}
      </AppButton>
      <AppButton
        v-if="job.project_id && projectName"
        class="button small ghost project-jump-btn"
        @click="$emit('open', job.project_id)"
      >
        Abrir
      </AppButton>
    </div>
  </li>
</template>

<style scoped>
.job-queue-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--line);
}
.job-queue-item:last-child {
  border-bottom: none;
}
.job-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.job-title-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.job-project-name {
  color: var(--muted);
  font-size: 13px;
}
.job-status-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.job-queue-pos {
  font-size: 12px;
  color: var(--muted);
}
.job-subtle-info {
  font-size: 12px;
  color: var(--muted);
}
.job-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
