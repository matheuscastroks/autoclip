import { request, post } from './client';
import type { Job } from '../types';

export const jobsApi = {
  list: () => request<Job[]>('/jobs'),
  start: (projectId: string, operation: string, options: Record<string, unknown> = {}) =>
    post<Job>(`/projects/${projectId}/jobs`, { operation, options }),
  cancel: (jobId: string) => post<Job>(`/jobs/${jobId}/cancel`),
  resume: (jobId: string, options?: { source_input?: string; candidate_id?: string }) =>
    post<Job>(`/jobs/${jobId}/resume`, options),
};
