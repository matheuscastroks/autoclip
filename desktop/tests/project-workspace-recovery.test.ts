import { mount } from '@vue/test-utils';
import { expect, it } from 'vitest';
import ProjectWorkspace from '../src/components/ProjectWorkspace.vue';

it('keeps preview recovery available across project tabs and retries the current selection', async () => {
  const analysis = {
    state: 'completed',
    analysis_hash: 'a'.repeat(64),
    proposals: [],
    topic_groups: [],
  };
  const selection = {
    schema_version: '1.0',
    analysis_hash: analysis.analysis_hash,
    candidate_ids: ['candidate-1'],
  };
  const w = mount(ProjectWorkspace, {
    props: {
      project: {
        id: 'project-1',
        name: 'Entrevista',
        status: 'completed',
        warnings: [],
        word_count: 12,
      },
      transcript: null,
      revisions: [],
      jobs: [],
      sourceUrl: '',
      previewUrl: '',
      busy: false,
      activeTab: 'transcript',
      analysis,
      selection,
      previewError: 'Dados inválidos ou pasta incompatível. Verifique sua seleção.',
    },
    global: {
      stubs: {
        WorkspaceHeader: true,
        ProjectTabs: true,
        TranscriptPanel: true,
        AnalysisPanel: true,
        ReviewPanel: true,
        PipelinePanel: true,
      },
    },
  });
  expect(w.get('[data-preview-failure]').text()).toContain('Não foi possível gerar as prévias');
  await w.get('[data-action=retry-previews]').trigger('click');
  expect(w.emitted('render')?.[0]?.[0]).toEqual({
    analysis_hash: analysis.analysis_hash,
    candidate_ids: ['candidate-1'],
  });
  expect(w.emitted('dismissPreviewError')).toHaveLength(1);
  w.unmount();
});
