import { mount, flushPromises } from '@vue/test-utils';
import { describe, it, expect, vi, afterEach } from 'vitest';
import App from '../src/App.vue';
import { api } from '../src/api';
afterEach(() => vi.restoreAllMocks());
const project = {
  id: 'p',
  name: 'Projeto fixture',
  title: 'Vídeo fixture',
  path: '/fixture',
  duration_us: 30000000,
  status: 'needs_review',
  has_transcript: true,
  word_count: 1,
  revisions: [],
  has_analysis: true,
  is_manual: false,
  warnings: [],
  created_at: '',
  updated_at: 0,
  source: {
    local_path: '/fixture.mp4',
    original_title: 'Fixture',
    channel: '',
    attribution: 'TEST ONLY',
    sha256: 'a'.repeat(64),
  },
  error: null,
};
const config = {
  asr_model_path: '/model',
  gemini_model: 'fixture',
  max_calls: 1,
  window_seconds: 600,
  max_text_chars: 60000,
  ffmpeg: '/ffmpeg',
  ffprobe: '/probe',
  asr_available: true,
  tools_available: true,
  gemini_key_configured: false,
};
const revisions = ['A', 'B'].map(id => ({
  revision_id: id,
  title: 'Corte ' + id,
  rationale: 'TEST ONLY',
  technical_pass: true,
  review_status: 'needs_review',
  duration_us: 20000000,
  start_us: 0,
  end_us: 20000000,
  caption_words: [],
  warnings: [],
  content_hash: 'a'.repeat(64),
}));
function setup() {
  vi.spyOn(api, 'projects').mockResolvedValue([project]);
  vi.spyOn(api, 'project').mockResolvedValue(project);
  vi.spyOn(api, 'config').mockResolvedValue(config);
  vi.spyOn(api, 'jobs').mockResolvedValue([]);
  vi.spyOn(api, 'transcript').mockResolvedValue({
    words: [{ id: 'w', text: 'Texto fixture', start_us: 0, end_us: 1000000 }],
    segments: [],
  });
  vi.spyOn(api, 'revisions').mockResolvedValue(revisions);
  vi.spyOn(api, 'media').mockImplementation(async (_pid, asset) => '/media/' + asset);
  vi.spyOn(api, 'decide').mockResolvedValue({});
  vi.spyOn(api, 'analysis').mockResolvedValue({
    schema_version: '1.0',
    state: 'not_started',
    job_id: null,
    analysis_hash: null,
    model: null,
    completed_windows: 0,
    total_windows: 0,
    topic_groups: [],
    proposals: [],
  });
  vi.spyOn(api, 'selection').mockResolvedValue({
    schema_version: '1.0',
    analysis_hash: null,
    candidate_ids: [],
  });
}
async function open() {
  const w = mount(App);
  await flushPromises();
  await w.get('[data-project-id=p]').trigger('click');
  await flushPromises();
  return w;
}
describe('review identity across refresh and failures', () => {
  it('sends library deletion to the trash', async () => {
    setup();
    Object.defineProperty(HTMLDialogElement.prototype, 'showModal', {
      configurable: true,
      value: vi.fn(),
    });
    Object.defineProperty(HTMLDialogElement.prototype, 'close', {
      configurable: true,
      value: vi.fn(),
    });
    vi.spyOn(api, 'deleteProject').mockResolvedValue({ deleted: true });
    const w = mount(App);
    await flushPromises();
    await w.get('[data-action=delete-project]').trigger('click');
    expect(w.text()).toContain('Mover projeto para a lixeira?');
    await w.get('.delete-confirm-action').trigger('click');
    await flushPromises();
    expect(api.deleteProject).toHaveBeenCalledWith('p');
    w.unmount();
  });
  it('keeps engine session and refresh in the top navigation disclosure', async () => {
    setup();
    const w = mount(App);
    await flushPromises();
    expect(w.find('.topbar').exists()).toBe(false);
    expect(w.get('.engine-popover .sidebar-session').text()).toContain('Sessão local');
    const before = vi.mocked(api.projects).mock.calls.length;
    await w.get('.engine-popover button[title="Atualizar projetos"]').trigger('click');
    await flushPromises();
    expect(vi.mocked(api.projects).mock.calls.length).toBe(before + 1);
    w.unmount();
  });
  it('does not reopen a project when navigation abandons an in-flight load', async () => {
    setup();
    let resolveProject: (value: typeof project) => void = () => {};
    vi.mocked(api.project).mockImplementation(
      () => new Promise(resolve => (resolveProject = resolve))
    );
    const w = mount(App);
    await flushPromises();
    await w.get('[data-project-id=p]').trigger('click');
    await w.get('nav button:nth-child(2)').trigger('click');
    resolveProject(project);
    await flushPromises();
    expect(w.get('h1').text()).toBe('Configurações');
    expect(w.find('[aria-label="Áreas do projeto"]').exists()).toBe(false);
    w.unmount();
  });
  it('starts analysis without a manual limit or consent checkbox', async () => {
    Object.defineProperty(HTMLDialogElement.prototype, 'showModal', {
      configurable: true,
      value: vi.fn(),
    });
    Object.defineProperty(HTMLDialogElement.prototype, 'close', {
      configurable: true,
      value: vi.fn(),
    });
    setup();
    vi.mocked(api.config).mockResolvedValue({ ...config, gemini_key_configured: true });
    vi.spyOn(api, 'start').mockResolvedValue({} as any);
    const w = await open();
    await w.get('[data-stage=analyze] button').trigger('click');
    await flushPromises();
    expect(w.text()).not.toContain('Histórico da análise Gemini');
    const dialog = w.findAll('dialog').find(d => d.text().includes('Analisar com Gemini'))!;
    expect(dialog.find('input[type=checkbox]').exists()).toBe(false);
    expect(dialog.text()).not.toContain('Limite de tentativas');
    expect(dialog.find('button[type="submit"]').text()).toContain('Iniciar análise');
    await dialog.get('form').trigger('submit');
    await flushPromises();
    expect(api.start).toHaveBeenCalledWith(
      'p',
      'analyze',
      expect.not.objectContaining({ max_calls: expect.anything() })
    );
    expect(vi.mocked(api.start).mock.calls[0][2]).not.toHaveProperty('authorize_text');
    w.unmount();
  });
  it('creates an automatic project without asking for a limit or checkbox', async () => {
    setup();
    vi.mocked(api.config).mockResolvedValue({ ...config, gemini_key_configured: true });
    Object.defineProperty(HTMLDialogElement.prototype, 'showModal', {
      configurable: true,
      value: vi.fn(),
    });
    Object.defineProperty(HTMLDialogElement.prototype, 'close', {
      configurable: true,
      value: vi.fn(),
    });
    vi.spyOn(api, 'create').mockResolvedValue({ project, job: {} as any });
    const w = mount(App);
    await flushPromises();
    await w.get('.new-project-action').trigger('click');
    const dialog = w.findAll('dialog').find(d => d.text().includes('Nome do projeto'))!;
    expect(dialog.find('input[type=checkbox]').exists()).toBe(false);
    expect(dialog.text()).not.toContain('Limite de tentativas');
    await dialog.get('input[maxlength="100"]').setValue('Projeto novo');
    await dialog.findAll('.source-switch button')[1].trigger('click');
    await dialog.get('input[type=url]').setValue('https://www.youtube.com/watch?v=fixture');
    await dialog.get('form').trigger('submit');
    await flushPromises();
    expect(api.create).toHaveBeenCalledWith(
      'Projeto novo',
      'https://www.youtube.com/watch?v=fixture',
      { automatic: true }
    );
    w.unmount();
  });
  it('loads original as soon as automatic import finishes while the job is still running', async () => {
    setup();
    const pending = {
      ...project,
      source: null,
      has_transcript: false,
      has_analysis: false,
      status: 'pending_import',
    };
    vi.mocked(api.projects).mockResolvedValue([pending]);
    vi.mocked(api.project).mockResolvedValue(pending);
    vi.mocked(api.revisions).mockResolvedValue([]);
    vi.mocked(api.jobs).mockResolvedValue([
      {
        id: 'j',
        project_id: 'p',
        operation: 'prepare',
        status: 'running',
        created_at: '',
        requests_used: 0,
        request_limit: 2,
        events: [],
      },
    ]);
    const w = await open();
    expect(w.find('video').exists()).toBe(false);
    const imported = { ...pending, source: project.source, status: 'processing' };
    vi.mocked(api.projects).mockResolvedValue([imported]);
    vi.mocked(api.project).mockResolvedValue(imported);
    await w.get('[title="Atualizar projetos"]').trigger('click');
    await flushPromises();
    expect(w.get('video').attributes('src')).toBe('/media/source');
    w.unmount();
  });
  it('offers download for selected B without editorial approval', async () => {
    setup();
    const w = await open();
    await w.get('#tab-cuts').trigger('click');
    await flushPromises();
    await w
      .findAll('.clip-item')
      .find(row => row.text().includes('Corte B'))!
      .trigger('click');
    await flushPromises();
    expect(w.get('.clip-preview > video').attributes('src')).toBe('/media/B');
    expect(w.find('[data-action=approve]').exists()).toBe(false);
    expect(w.get('a[download]').attributes('href')).toBe('/media/B?download=1');
    expect(w.get('.clip-preview > video').attributes('src')).toBe('/media/B');
    expect(w.get('.clip-item.selected').text()).toContain('Corte B');
    w.unmount();
  });
  it('ignores stale media responses when rapidly selecting A then B', async () => {
    setup();
    const w = await open();
    await w.get('#tab-cuts').trigger('click');
    await flushPromises();
    let resolveA: (value: string) => void = () => {},
      resolveB: (value: string) => void = () => {};
    vi.mocked(api.media).mockImplementation(
      (_p, asset) =>
        new Promise(resolve => {
          if (asset === 'A') resolveA = resolve;
          else resolveB = resolve;
        })
    );
    await w
      .findAll('.clip-item')
      .find(row => row.text().includes('Corte A'))!
      .trigger('click');
    await w
      .findAll('.clip-item')
      .find(row => row.text().includes('Corte B'))!
      .trigger('click');
    resolveB('/media/B');
    await flushPromises();
    resolveA('/media/A');
    await flushPromises();
    expect(w.get('.clip-preview > video').attributes('src')).toBe('/media/B');
    w.unmount();
  });
  it('keeps transcript and original when revisions endpoint fails', async () => {
    setup();
    vi.mocked(api.revisions).mockRejectedValue(new Error('Preview damaged'));
    const w = await open();
    expect(w.find('video').attributes('src')).toBe('/media/source');
    await w.get('[role=tablist] button:nth-child(2)').trigger('click');
    await flushPromises();
    expect(w.text()).toContain('Texto fixture');
    w.unmount();
  });
});
