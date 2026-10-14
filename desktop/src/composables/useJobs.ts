import { ref, computed } from 'vue';
import { api } from '../api';
import type { Job } from '../types';
import { active } from '../format';
import { createJobNotifier } from '../notifications';

export function useJobs() {
  const jobs = ref<Job[]>([]);
  const reportJobs = createJobNotifier();

  const activeJobsCount = computed(() => jobs.value.filter(j => active(j.status)).length);
  const running = computed(() => jobs.value.some(j => active(j.status)));

  function updateJobs(newJobs: Job[]) {
    jobs.value = newJobs;
    reportJobs(newJobs);
  }

  async function cancelJob(id: string) {
    return api.cancel(id);
  }

  async function resumeJob(id: string, options?: { source_input?: string; candidate_id?: string }) {
    return api.resume(id, options);
  }

  return {
    jobs,
    activeJobsCount,
    running,
    updateJobs,
    cancelJob,
    resumeJob,
  };
}
