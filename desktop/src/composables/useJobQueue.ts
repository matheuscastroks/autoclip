import { computed, type Ref } from 'vue';
import type { Job } from '../types';
import { active } from '../format';

export function useJobQueue(jobsRef: Ref<Job[]>) {
  const activeJobs = computed(() =>
    jobsRef.value
      .filter(j => active(j.status))
      .sort((a, b) => a.created_at.localeCompare(b.created_at))
  );

  const runningCount = computed(
    () => jobsRef.value.filter(j => j.status === 'running').length
  );

  const pendingCount = computed(
    () => jobsRef.value.filter(j => j.status === 'pending').length
  );

  const recentJobs = computed(() =>
    [...jobsRef.value]
      .sort((a, b) => b.created_at.localeCompare(a.created_at))
      .slice(0, 20)
  );

  return {
    activeJobs,
    runningCount,
    pendingCount,
    recentJobs,
  };
}
