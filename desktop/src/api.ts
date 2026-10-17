import { initializeSession, ApiError, request } from './api/client';
import { projectsApi } from './api/projects';
import { jobsApi } from './api/jobs';
import { configApi } from './api/config';
import { systemApi } from './api/system';

export { initializeSession, ApiError, request };
export { projectsApi, jobsApi, configApi, systemApi };

/**
 * Fachada retrocompatível para a camada de componentes existente.
 * Permite refatoração gradual sem quebrar nenhum consumidor.
 */
export const api = {
  // Projetos
  projects: projectsApi.list,
  project: projectsApi.get,
  importProject: projectsApi.import,
  create: projectsApi.create,
  deleteProject: projectsApi.delete,
  deletePermanent: projectsApi.deletePermanent,
  trash: projectsApi.trash,
  restoreProject: projectsApi.restore,
  openFolder: projectsApi.openFolder,

  // Mídia e Revisões
  transcript: projectsApi.transcript,
  updateTranscript: projectsApi.updateTranscript,
  analysis: projectsApi.analysis,
  selection: projectsApi.selection,
  saveSelection: projectsApi.saveSelection,
  revisions: projectsApi.revisions,
  media: projectsApi.media,
  deleteClip: projectsApi.deleteClip,
  bulkDeleteClips: projectsApi.bulkDeleteClips,
  bulkExportClips: projectsApi.bulkExportClips,
  deletedClips: projectsApi.deletedClips,
  restoreClip: projectsApi.restoreClip,
  decide: projectsApi.decide,

  // Jobs
  jobs: jobsApi.list,
  start: jobsApi.start,
  cancel: jobsApi.cancel,
  resume: jobsApi.resume,
  clearJobHistory: jobsApi.clearHistory,

  // Configuração
  config: configApi.get,
  saveConfig: configApi.save,
  saveKey: configApi.saveGeminiKey,
  saveOpenRouterKey: configApi.saveOpenRouterKey,
  geminiConnection: configApi.geminiConnection,
  testGemini: configApi.testGemini,

  // Sistema e Provisionamento
  systemProfile: systemApi.profile,
  provision: systemApi.provision,
  provisionStatus: systemApi.provisionStatus,
  cancelProvision: systemApi.cancelProvision,
  pick: systemApi.pick,
  shutdown: systemApi.shutdown,
};
