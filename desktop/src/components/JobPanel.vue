<script setup lang="ts">
import AppIcon from './ui/AppIcon.vue';
import AppButton from './AppButton.vue';
import { watch } from 'vue';
import { notifyJob } from '../notifications';
import type { Job } from '../types';
import { labels, stages, active } from '../format';
const props = defineProps<{ jobs: Job[] }>();
defineEmits<{ cancel: [id: string]; resume: [id: string] }>();
watch(
  () => props.jobs,
  jobs => {
    for (const job of jobs) if (['failed', 'interrupted'].includes(job.status)) notifyJob(job);
  },
  { immediate: true }
);
</script>
<template>
  <div v-if="jobs.length" class="job-list">
    <article
      v-for="job in jobs.slice(0, 5)"
      :key="job.id"
      class="job"
      :class="{ 'job-failed': job.status === 'failed' }"
    >
      <AppIcon v-if="active(job.status)" name="spinner" size="md" class="spin" /><AppIcon
        v-else-if="job.status === 'completed'"
        name="check-circle"
        size="md"
      /><AppIcon v-else name="warning" size="md" />
      <div class="job-copy">
        <strong>{{ stages[job.stage || job.operation] || job.operation }}</strong>
        <span>
          <el-tag
            size="small"
            :type="
              job.status === 'completed'
                ? 'success'
                : job.status === 'failed'
                  ? 'danger'
                  : active(job.status)
                    ? 'primary'
                    : 'info'
            "
            effect="dark"
            style="margin-right: 4px"
          >
            {{ labels[job.status] || job.status }}
          </el-tag>
          <template v-if="job.operation === 'analyze'">
            · {{ job.requests_used || 0 }} chamada(s){{
              job.request_mode === 'automatic'
                ? ' · planejamento automático'
                : ' de ' + job.request_limit
            }}</template
          >
        </span>
        <AppButton v-if="job.error" type="button" class="text-button" @click="notifyJob(job, true)"
          >Ver motivo da falha</AppButton
        >
        <p v-if="job.exports?.length">
          {{ job.exports.length }} pacote(s) exportado(s). Abra a pasta do projeto.
        </p>
      </div>
      <AppButton
        v-if="active(job.status)"
        class="button small secondary"
        :disabled="job.status === 'cancelling'"
        @click="$emit('cancel', job.id)"
        ><AppIcon name="stop" size="sm" />Cancelar</AppButton
      >
      <AppButton
        v-else-if="
          ['failed', 'cancelled', 'interrupted'].includes(job.status) && job.operation !== 'analyze'
        "
        class="button small secondary"
        data-action="resume"
        @click="$emit('resume', job.id)"
        ><AppIcon name="refresh" size="sm" />Retomar</AppButton
      >
    </article>
  </div>
</template>
