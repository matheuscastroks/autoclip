import { mount } from '@vue/test-utils';
import { describe, it, expect, vi } from 'vitest';
import { notify, resetNotifications } from '../src/notifications';
import ProjectWorkspace from '../src/components/ProjectWorkspace.vue';
import ProjectLibrary from '../src/components/ProjectLibrary.vue';
const project = {
  id: 'p',
  name: 'Teste',
  title: 'Entrevista',
  path: '/fixture',
  duration_us: 30000000,
  status: 'processing',
  has_transcript: false,
  word_count: 0,
  revisions: [],
  has_analysis: false,
  is_manual: false,
  warnings: [],
  created_at: '',
  updated_at: 0,
  source: null,
  error: null,
};
describe('workflow visibility', () => {
  it('distinguishes pipeline readiness from editorial decisions and an unstarted analysis', () => {
    const w = mount(ProjectWorkspace, {
      props: {
        project: { ...project, status: 'needs_review', has_transcript: true },
        transcript: null,
        revisions: [],
        jobs: [],
        busy: false,
        sourceUrl: '',
        previewUrl: '',
        analysis: {
          schema_version: '1.0',
          state: 'not_started',
          job_id: null,
          analysis_hash: null,
          model: null,
          completed_windows: 0,
          total_windows: 0,
          topic_groups: [],
          proposals: [],
        },
      },
    });
    expect(w.text()).toContain('Cortes gerados');
    expect(w.get('.analysis-metric-item .metric-label').text()).toBe('Análise ainda não iniciada');
    expect(w.text()).not.toContain('Revisão editorial pendente');
    w.unmount();
  });

  it('keeps the active tab and panel associated while switching project areas', async () => {
    const w = mount(ProjectWorkspace, {
      props: {
        project,
        transcript: null,
        revisions: [],
        jobs: [],
        sourceUrl: '',
        previewUrl: '',
        busy: false,
      },
    });

    for (const [tabId, contentSelector] of [
      ['tab-transcript', '.transcript-layout'],
      ['tab-analysis', '.analysis-workspace'],
      ['tab-cuts', '.cuts-empty'],
    ]) {
      await w.get(`#${tabId}`).trigger('click');
      expect(w.get(`#${tabId}`).attributes('aria-selected')).toBe('true');
      expect(w.get('#project-panel').attributes('aria-labelledby')).toBe(tabId);
      expect(w.find(contentSelector).exists()).toBe(true);
    }

    w.unmount();
  });

  it('offers access to the project trash from the library', async () => {
    const w = mount(ProjectLibrary, { props: { projects: [project], busy: false } });
    await w.get('[data-action=open-project-trash]').trigger('click');
    expect(w.emitted('trash')).toHaveLength(1);
    w.unmount();
  });
  it('shows failed import with recovery and places small video inside preparation', async () => {
    resetNotifications();
    const errorToast = vi.spyOn(notify, 'error');
    const w = mount(ProjectWorkspace, {
      props: {
        project: { ...project, status: 'failed' },
        transcript: null,
        revisions: [],
        jobs: [
          {
            id: 'j',
            project_id: 'p',
            operation: 'prepare',
            status: 'failed',
            created_at: '',
            requests_used: 0,
            request_limit: null,
            events: [],
            error: {
              code: 'SOURCE_AUTH_REQUIRED',
              message: 'YouTube bloqueou o download. Use um arquivo local.',
            },
            progress: {
              stage: 'import',
              steps: { import: 'failed', transcribe: 'pending', analyze: 'pending' },
            },
          },
        ],
        sourceUrl: '',
        previewUrl: '',
        busy: false,
      },
    });
    expect(w.text()).not.toContain('Importação em andamento');
    expect(w.find('.original-column').exists()).toBe(false);
    expect(w.find('.pipeline-panel .pipeline-video').exists()).toBe(true);
    expect(w.get('[data-stage=import]').text()).not.toContain('YouTube bloqueou');
    expect(errorToast).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({ description: 'YouTube bloqueou o download. Use um arquivo local.' })
    );
    await w.get('[data-action=error-details]').trigger('click');
    expect(errorToast).toHaveBeenLastCalledWith(
      expect.any(String),
      expect.objectContaining({ force: true })
    );
    await w.get('[data-action=retry-import]').trigger('click');
    expect(w.emitted('resume')?.[0]).toEqual(['j']);
    await w.get('[data-action=replace-source]').trigger('click');
    expect(w.emitted('replaceSource')?.[0]).toEqual(['j']);
    expect(w.get('[data-stage=transcribe]').text()).toContain('Na fila');
    w.unmount();
  });
  it('offers final export only when an editorially approved preview exists', () => {
    const revisions = [
      {
        revision_id: 'a',
        title: 'A',
        technical_pass: true,
        review_status: 'approved',
        warnings: [],
      },
      {
        revision_id: 'b',
        title: 'B',
        technical_pass: true,
        review_status: 'needs_review',
        warnings: [],
      },
    ];
    const w = mount(ProjectWorkspace, {
      props: {
        project,
        transcript: null,
        revisions,
        jobs: [],
        sourceUrl: '',
        previewUrl: '',
        busy: false,
      },
    });
    expect(w.find('[data-stage=review]').exists()).toBe(false);
    expect(w.get('[data-stage=export]').text()).toContain('Exportar aprovados');
    w.unmount();
  });
  it.each(['running', 'completed'])(
    'does not show an old project error while the current job is %s',
    status => {
      const oldFailure = {
        ...project,
        error: { code: 'PROVIDER_UNAVAILABLE', message: 'Falha antiga' },
      };
      const w = mount(ProjectWorkspace, {
        props: {
          project: oldFailure,
          transcript: null,
          revisions: [],
          jobs: [
            {
              id: 'j',
              project_id: 'p',
              operation: 'analyze',
              status,
              created_at: '',
              requests_used: 1,
              request_limit: 28,
              events: [],
            },
          ],
          sourceUrl: '',
          previewUrl: '',
          busy: status === 'running',
        },
      });
      expect(w.text()).not.toContain('PROVIDER_UNAVAILABLE');
      w.unmount();
    }
  );
  it('keeps stage activity and cancellation beside the video', () => {
    const w = mount(ProjectWorkspace, {
      props: {
        project,
        transcript: null,
        revisions: [],
        jobs: [
          {
            id: 'j',
            project_id: 'p',
            operation: 'prepare',
            status: 'running',
            created_at: '',
            requests_used: 0,
            request_limit: 10,
            events: [],
            progress: {
              stage: 'transcribe',
              steps: {
                import: 'completed',
                transcribe: 'running',
                analyze: 'pending',
                render: 'pending',
              },
            },
          },
        ],
        sourceUrl: '',
        previewUrl: '',
        busy: true,
      },
    });
    expect(
      w.get('.pipeline-panel [data-stage=transcribe] [role=progressbar]').attributes('aria-label')
    ).toContain('Transcrever');
    expect(w.get('.pipeline-panel').text()).toContain('Cancelar');
    expect(w.find('.project-jobs').exists()).toBe(false);
  });
  it('uses actual covers and provides project deletion without opening it', async () => {
    const w = mount(ProjectLibrary, {
      props: { projects: [project], busy: false, covers: { p: '/thumbnail.jpg' } },
    });
    expect(w.get('img').attributes('src')).toBe('/thumbnail.jpg');
    await w.get('[data-action=delete-project]').trigger('click');
    expect(w.emitted('delete')?.[0]).toEqual(['p']);
    expect(w.emitted('open')).toBeUndefined();
  });
  it('stops an animated bar when the worker was forcibly cancelled', () => {
    const w = mount(ProjectWorkspace, {
      props: {
        project,
        transcript: null,
        revisions: [],
        jobs: [
          {
            id: 'j',
            project_id: 'p',
            operation: 'prepare',
            status: 'cancelled',
            created_at: '',
            requests_used: 0,
            request_limit: 10,
            events: [],
            progress: {
              stage: 'transcribe',
              steps: {
                import: 'completed',
                transcribe: 'running',
                analyze: 'pending',
                render: 'pending',
              },
            },
          },
        ],
        sourceUrl: '',
        previewUrl: '',
        busy: false,
      },
    });
    expect(w.get('[data-stage=transcribe]').text()).toContain('Cancelado');
    expect(w.get('[data-stage=transcribe] .stage-progress').classes()).not.toContain(
      'indeterminate'
    );
  });
  it('does not mark completed or pending stages as failed after an analysis failure', () => {
    const imported = {
      ...project,
      has_transcript: true,
      source: {
        local_path: '/fixture',
        original_title: 'Fixture',
        channel: '',
        attribution: '',
        sha256: 'a'.repeat(64),
      },
    };
    const w = mount(ProjectWorkspace, {
      props: {
        project: imported,
        transcript: null,
        revisions: [],
        jobs: [
          {
            id: 'j',
            project_id: 'p',
            operation: 'analyze',
            status: 'failed',
            created_at: '',
            requests_used: 0,
            request_limit: 1,
            events: [],
            progress: {
              stage: 'analyze',
              steps: {
                import: 'pending',
                transcribe: 'pending',
                analyze: 'failed',
                render: 'pending',
              },
            },
          },
        ],
        sourceUrl: '',
        previewUrl: '',
        busy: false,
      },
    });
    expect(w.get('[data-stage=import]').text()).toContain('Concluído');
    expect(w.get('[data-stage=transcribe]').text()).toContain('Concluído');
    expect(w.get('[data-stage=render]').text()).toContain('Na fila');
    w.unmount();
  });
  it('renders linear progression stepper track with step states', () => {
    const imported = {
      ...project,
      has_transcript: true,
      source: {
        local_path: '/fixture',
        original_title: 'Fixture',
        channel: '',
        attribution: '',
        sha256: 'a'.repeat(64),
      },
    };
    const w = mount(ProjectWorkspace, {
      props: {
        project: imported,
        transcript: null,
        revisions: [],
        jobs: [],
        sourceUrl: '',
        previewUrl: '',
        busy: false,
      },
    });
    expect(w.find('.stepper-track-wrap').exists()).toBe(true);
    expect(w.text()).toContain('Esteira de Processamento');
    const nodes = w.findAll('.stepper-node');
    expect(nodes.length).toBe(6);
    expect(nodes[0].attributes('data-state')).toBe('completed');
    expect(nodes[1].attributes('data-state')).toBe('completed');
    expect(nodes[2].attributes('data-state')).toBe('pending');
    w.unmount();
  });
});
