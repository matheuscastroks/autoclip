import { request, post, put, del } from './client';
import type {
  Project,
  Revision,
  Transcript,
  AnalysisView,
  AnalysisSelection,
  Decision,
} from '../types';

export const projectsApi = {
  list: () => request<Project[]>('/projects'),
  get: (id: string) => request<Project>(`/projects/${id}`),
  create: (name: string, source_input: string, options: Record<string, unknown> = {}) =>
    post<{ project: Project; job: import('../types').Job }>('/projects', {
      name,
      source_input,
      ...options,
    }),
  import: (path: string) => post<Project>('/projects/import', { path }),
  delete: (id: string) => del<{ deleted: boolean }>(`/projects/${id}?permanent=false`),
  deletePermanent: (id: string) => del<{ deleted: boolean }>(`/projects/${id}?permanent=true`),
  trash: () => request<{ id: string; name: string; deleted_at: string }[]>('/trash'),
  restore: (id: string) => post<void>(`/trash/${id}/restore`),
  openFolder: (id: string) => post<void>(`/projects/${id}/open-folder`),
  transcript: (id: string) => request<Transcript>(`/projects/${id}/transcript`),
  analysis: (id: string) => request<AnalysisView>(`/projects/${id}/analysis`),
  selection: (id: string) => request<AnalysisSelection>(`/projects/${id}/analysis-selection`),
  saveSelection: (id: string, value: AnalysisSelection) =>
    put<AnalysisSelection>(`/projects/${id}/analysis-selection`, {
      analysis_hash: value.analysis_hash,
      candidate_ids: value.candidate_ids,
    }),
  revisions: (id: string) => request<Revision[]>(`/projects/${id}/revisions`),
  media: async (id: string, asset: string) =>
    (await request<{ url: string }>(`/projects/${id}/media/${asset}/ticket`)).url,
  deleteClip: (pid: string, rid: string) => del<void>(`/projects/${pid}/revisions/${rid}`),
  bulkDeleteClips: (pid: string, ids: string[]) =>
    post<void>(`/projects/${pid}/revisions/bulk-delete`, { revision_ids: ids }),
  bulkExportClips: (pid: string, ids: string[]) =>
    post<void>(`/projects/${pid}/revisions/bulk-export`, { revision_ids: ids }),
  deletedClips: (pid: string) =>
    request<{ revision_id: string; title: string }[]>(`/projects/${pid}/deleted-revisions`),
  restoreClip: (pid: string, rid: string) =>
    post<void>(`/projects/${pid}/revisions/${rid}/restore`),
  decide: (id: string, decision: Decision) =>
    post<unknown>(`/projects/${id}/revisions/${decision.revision_id}/decision`, {
      decision: decision.decision,
      checks: decision.checks,
      notes: decision.notes,
      content_hash: decision.content_hash,
    }),
};
