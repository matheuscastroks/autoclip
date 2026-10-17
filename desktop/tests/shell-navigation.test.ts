import { flushPromises, mount } from '@vue/test-utils';
import { afterEach, expect, it, vi } from 'vitest';
import App from '../src/App.vue';
import { api } from '../src/api';

const project = {
  id: 'p',
  name: 'Entrevista',
  title: 'Entrevista',
  path: '/fixture',
  duration_us: 30000000,
  status: 'analyzed',
  has_transcript: false,
  has_analysis: false,
  word_count: 0,
  revisions: [],
  is_manual: false,
  warnings: [],
  created_at: '',
  updated_at: 0,
  source: null,
  error: null,
};
vi.mock('../src/api', () => ({
  api: {
    projects: vi.fn(async () => [project]),
    jobs: vi.fn(async () => []),
    systemProfile: vi.fn(async () => ({ profile: null })),
    bulkExportClips: vi.fn(async () => ({})),
    project: vi.fn(async () => project),
    revisions: vi.fn(async () => []),
    analysis: vi.fn(async () => null),
    selection: vi.fn(async () => ({
      schema_version: '1.0',
      analysis_hash: 'a'.repeat(64),
      candidate_ids: ['c1'],
    })),
    config: vi.fn(async () => ({
      asr_available: true,
      tools_available: true,
      gemini_key_configured: true,
      asr_model_path: '/model',
      ffmpeg: '/ffmpeg',
      ffprobe: '/probe',
      gemini_model: 'fixture',
      max_calls: 10,
      window_seconds: 600,
      max_text_chars: 60000,
    })),
  },
}));

afterEach(() => {
  vi.unstubAllGlobals();
});

it('finishes hydrating the retained project when global navigation changes mid-load', async () => {
  let resolveSelection!: (value: {
    schema_version: string;
    analysis_hash: string;
    candidate_ids: string[];
  }) => void;
  vi.mocked(api.selection).mockImplementationOnce(
    () =>
      new Promise(resolve => {
        resolveSelection = resolve;
      })
  );
  vi.stubGlobal('matchMedia', () => ({
    matches: false,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  }));
  const w = mount(App, { attachTo: document.body });
  try {
    await flushPromises();
    await w.get('[data-project-id=p]').trigger('click');
    await flushPromises();
    await w.get('[aria-label="Configurações"]').trigger('click');
    await flushPromises();
    resolveSelection({
      schema_version: '1.0',
      analysis_hash: 'a'.repeat(64),
      candidate_ids: ['c2'],
    });
    await flushPromises();
    await w.get('[aria-label="Projetos"]').trigger('click');
    await flushPromises();
    const workspace = w.findComponent({ name: 'ProjectWorkspace' });
    expect(workspace.props('selection')?.candidate_ids).toEqual(['c2']);
    expect(workspace.props('mediaLoading')).toBe(false);
  } finally {
    w.unmount();
  }
});

it('finishes artifact loading after leaving an already opened project', async () => {
  let finishArtifacts!: () => void;
  vi.mocked(api.revisions).mockImplementationOnce(
    () =>
      new Promise(resolve => {
        finishArtifacts = () => resolve([]);
      })
  );
  vi.stubGlobal('matchMedia', () => ({
    matches: false,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  }));
  const w = mount(App, { attachTo: document.body });
  try {
    await flushPromises();
    await w.get('[data-project-id=p]').trigger('click');
    await flushPromises();
    await w.get('[aria-label="Configurações"]').trigger('click');
    await flushPromises();
    finishArtifacts();
    await flushPromises();
    await w.get('[aria-label="Projetos"]').trigger('click');
    await flushPromises();
    expect(w.findComponent({ name: 'ProjectWorkspace' }).props('mediaLoading')).toBe(false);
    expect(w.findComponent({ name: 'ProjectWorkspace' }).props('selection')?.candidate_ids).toEqual(
      ['c1']
    );
  } finally {
    w.unmount();
  }
});

it('returns from Settings to the same project tab and keeps the queue accessible', async () => {
  vi.stubGlobal('matchMedia', () => ({
    matches: false,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  }));
  const w = mount(App, { attachTo: document.body });
  try {
    await flushPromises();
    await w.get('[data-project-id=p]').trigger('click');
    await flushPromises();
    await w.get('#tab-cuts').trigger('click');
    await w
      .findAll('button')
      .find(b => b.text() === 'Configurações' || b.attributes('aria-label') === 'Configurações')!
      .trigger('click');
    await flushPromises();
    await w.get('[title="Fila global de tarefas"]').trigger('click');
    await flushPromises();
    expect(w.findComponent({ name: 'GlobalQueueModal' }).exists()).toBe(true);
    await w
      .findAll('button')
      .find(b => b.attributes('aria-label') === 'Projetos' || b.text().startsWith('Projetos'))!
      .trigger('click');
    await flushPromises();
    expect(w.get('#tab-cuts').attributes('aria-selected')).toBe('true');
    expect(w.get('h1').text()).toBe('Entrevista');
    expect(w.findComponent({ name: 'ProjectWorkspace' }).props('selection').candidate_ids).toEqual([
      'c1',
    ]);
    await w.get('[aria-label="Todos os projetos"]').trigger('click');
    await flushPromises();
    expect(w.find('[data-project-id=p]').exists()).toBe(true);
  } finally {
    w.unmount();
  }
});

it('does not leave Settings when polling reloads artifacts after a job completes', async () => {
  vi.useFakeTimers();
  vi.mocked(api.jobs).mockResolvedValueOnce([
    { id: 'j', project_id: 'p', operation: 'analyze', status: 'running', events: [] } as never,
  ]);
  vi.stubGlobal('matchMedia', () => ({
    matches: false,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  }));
  const w = mount(App, { attachTo: document.body });
  try {
    await flushPromises();
    await w.get('[data-project-id=p]').trigger('click');
    await flushPromises();
    await w.get('[aria-label="Configurações"]').trigger('click');
    await flushPromises();
    vi.mocked(api.jobs).mockResolvedValue([
      { id: 'j', project_id: 'p', operation: 'analyze', status: 'completed', events: [] } as never,
    ]);
    await vi.advanceTimersByTimeAsync(3000);
    await flushPromises();
    expect(w.get('[aria-label="Configurações"]').attributes('aria-current')).toBe('page');
    expect(w.find('#tab-overview').exists()).toBe(false);
  } finally {
    w.unmount();
    vi.useRealTimers();
    vi.mocked(api.jobs).mockResolvedValue([]);
  }
});

it('keeps Settings active when an export operation completes in the background', async () => {
  let finish!: () => void;
  vi.mocked(api.bulkExportClips).mockImplementationOnce(
    () =>
      new Promise(resolve => {
        finish = () => resolve({});
      })
  );
  vi.stubGlobal('matchMedia', () => ({
    matches: false,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  }));
  const w = mount(App, { attachTo: document.body });
  try {
    await flushPromises();
    await w.get('[data-project-id=p]').trigger('click');
    await flushPromises();
    w.findComponent({ name: 'ProjectWorkspace' }).vm.$emit('bulkExport', ['r']);
    await flushPromises();
    await w.get('[aria-label="Configurações"]').trigger('click');
    await flushPromises();
    finish();
    await flushPromises();
    expect(w.get('[aria-label="Configurações"]').attributes('aria-current')).toBe('page');
    expect(w.find('#tab-overview').exists()).toBe(false);
  } finally {
    w.unmount();
  }
});

it('returns to the project library when clicking the Projects rail button while inside an open project', async () => {
  vi.stubGlobal('matchMedia', () => ({
    matches: false,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  }));
  const w = mount(App, { attachTo: document.body });
  try {
    await flushPromises();
    // Open project
    await w.get('[data-project-id=p]').trigger('click');
    await flushPromises();
    expect(w.findComponent({ name: 'ProjectWorkspace' }).exists()).toBe(true);

    // Click on Projects icon in the sidebar rail
    await w.get('[aria-label="Projetos"]').trigger('click');
    await flushPromises();

    // Verify it navigated back to the project library list
    expect(w.findComponent({ name: 'ProjectWorkspace' }).exists()).toBe(false);
    expect(w.findComponent({ name: 'ProjectLibrary' }).exists()).toBe(true);
  } finally {
    w.unmount();
  }
});
