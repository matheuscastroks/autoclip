import { mount, flushPromises } from '@vue/test-utils';
import { describe, it, expect, vi } from 'vitest';
import ProjectLibrary from '../src/components/ProjectLibrary.vue';
import SettingsPanel from '../src/components/SettingsPanel.vue';
import JobPanel from '../src/components/JobPanel.vue';
import ReviewPanel from '../src/components/ReviewPanel.vue';
import { notify, resetNotifications } from '../src/notifications';

const project = {
  id: 'p',
  name: 'Projeto de teste',
  title: 'Entrevista',
  path: '/fixture',
  duration_us: 30000000,
  status: 'failed',
  has_transcript: true,
  word_count: 100,
  revisions: [],
  has_analysis: false,
  is_manual: false,
  warnings: [],
  created_at: '2026-10-12T12:00:00Z',
  updated_at: 0,
  source: null,
  error: null,
};
const config = {
  asr_model_path: '/model',
  gemini_model: 'gemini-2.5-flash',
  max_calls: 10,
  window_seconds: 600,
  max_text_chars: 60000,
  ffmpeg: '/ffmpeg',
  ffprobe: '/ffprobe',
  asr_available: true,
  tools_available: true,
  gemini_key_configured: true,
};
describe('workspace interactions', () => {
  it('places publication copy and download in an on-demand Drawer', async () => {
    const w = mount(ReviewPanel, {
      props: {
        revisions: [
          {
            revision_id: 'r',
            title: 'Corte',
            technical_pass: true,
            review_status: 'needs_review',
            warnings: [],
          },
        ],
        manual: false,
        mediaUrl: '/r.mp4',
        sourceUrl: '',
      },
    });
    expect(w.find('video').exists()).toBe(false);
    await w.get('.clip-item').trigger('click');
    await flushPromises();
    expect(w.get('.clip-drawer-heading .preview-label').text()).toBe('Corte');
    expect(w.find('.clip-information .review-editorial').exists()).toBe(false);
    expect(w.find('a[download]').exists()).toBe(true);
    w.unmount();
  });
  it('aligns the reviewed cut with an external sidebar selection outside the filter', async () => {
    const rows = [
      {
        revision_id: 'a',
        title: 'Para conferir',
        technical_pass: true,
        review_status: 'needs_review',
        warnings: [],
        content_hash: 'a',
      },
      {
        revision_id: 'b',
        title: 'Aprovada',
        technical_pass: true,
        review_status: 'approved',
        warnings: [],
        content_hash: 'b',
      },
    ];
    const w = mount(ReviewPanel, {
      props: {
        revisions: rows,
        manual: false,
        mediaUrl: '/a.mp4',
        sourceUrl: '',
        selectedRevision: 'a',
      },
    });
    await w.findAll('.clip-item')[0].trigger('click');
    await flushPromises();
    await w
      .findAll('.cuts-filters button')
      .find(b => b.text() === 'Aprovados')!
      .trigger('click');
    await w.setProps({ selectedRevision: 'b', mediaUrl: '/b.mp4' });
    expect(w.get('.preview-label').text()).toBe('Aprovada');
    expect(w.get('.clip-preview>video').attributes('src')).toBe('/b.mp4');
    expect(w.find('[data-action=approve]').exists()).toBe(false);
    w.unmount();
  });
  it('filters projects by name and opens a real row', async () => {
    const w = mount(ProjectLibrary, { props: { projects: [project], busy: false } });
    await w.get('input[type=search]').setValue('inexistente');
    expect(w.text()).not.toContain('Entrevista');
    await w.get('input[type=search]').setValue('Entrevista');
    await w.get('[data-project-id=p]').trigger('click');
    expect(w.emitted('open')?.[0]).toEqual(['p']);
  });
  it('shows an honest empty library', () => {
    const w = mount(ProjectLibrary, { props: { projects: [], busy: false } });
    expect(w.text()).toContain('Nenhum projeto');
    expect(w.findAll('[data-project-id]').length).toBe(0);
  });
  it('masks a key and clears it after saving without localStorage', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const w = mount(SettingsPanel, {
      props: { config, saveConfig: vi.fn(), saveKey: save, pick: vi.fn() },
    });
    const input = w.get('input[type=password]');
    await input.setValue('fixture-secret');
    await w.get('[data-action=save-key]').trigger('click');
    await vi.waitFor(() => expect(save).toHaveBeenCalledWith('fixture-secret'));
    await vi.waitFor(() => expect((input.element as HTMLInputElement).value).toBe(''));
    expect(JSON.stringify(localStorage)).not.toContain('fixture-secret');
  });
  it('shows task failure and emits an explicit resume', async () => {
    resetNotifications();
    const errorToast = vi.spyOn(notify, 'error');
    const w = mount(JobPanel, {
      props: {
        jobs: [
          {
            id: 'j',
            project_id: 'p',
            status: 'failed',
            operation: 'transcribe',
            requests_used: 0,
            request_limit: 10,
            created_at: '',
            events: [],
            error: { code: 'MODEL_MISSING', message: 'Modelo indisponível' },
          },
        ],
      },
    });
    expect(w.text()).not.toContain('Modelo indisponível');
    expect(errorToast).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({ description: 'Modelo indisponível' })
    );
    await w.get('[data-action=resume]').trigger('click');
    expect(w.emitted('resume')?.[0]).toEqual(['j']);
  });
  it('does not offer semantic approval for a manual preview', () => {
    const w = mount(ReviewPanel, {
      props: { revisions: [], manual: true, mediaUrl: '', sourceUrl: '' },
    });
    expect(w.text()).toContain('Prévia manual');
    expect(w.find('[data-action=approve]').exists()).toBe(false);
  });
  it('allows technically valid download without editorial checks', async () => {
    const w = mount(ReviewPanel, {
      props: {
        manual: false,
        mediaUrl: '/fixture-preview.mp4',
        sourceUrl: '',
        revisions: [
          {
            revision_id: 'r',
            title: 'Corte teste',
            rationale: 'Fixture somente',
            technical_pass: true,
            review_status: 'needs_review',
            duration_us: 30000000,
            start_us: 0,
            end_us: 30000000,
            caption_words: [],
            warnings: [],
            content_hash: 'fixture',
          },
        ],
      },
    });
    expect(w.find('[data-action=approve]').exists()).toBe(false);
    await w.get('.clip-item').trigger('click');
    await flushPromises();
    expect(w.get('a[download]').attributes('href')).toBe('/fixture-preview.mp4?download=1');
    expect(w.emitted('decision')).toBeUndefined();
  });
  it('shows selection pending instead of fake clips', () => {
    const w = mount(ReviewPanel, {
      props: { revisions: [], manual: false, mediaUrl: '', sourceUrl: '' },
    });
    expect(w.text()).toContain('Nenhum corte disponível');
  });
});
