import { flushPromises, mount } from '@vue/test-utils';
import { beforeEach, expect, it, vi } from 'vitest';
import App from '../src/App.vue';
import { api } from '../src/api';
import NewProjectDialog from '../src/components/dialogs/NewProjectDialog.vue';
import OnboardingModal from '../src/components/OnboardingModal.vue';

vi.mock('../src/api', () => ({
  api: {
    projects: vi.fn(async () => []),
    jobs: vi.fn(async () => []),
    systemProfile: vi.fn(async () => ({ profile: null })),
    config: vi.fn(async () => ({
      asr_model_path: '/model',
      ffmpeg: '/ffmpeg',
      ffprobe: '/probe',
      gemini_model: 'fixture',
      max_calls: 10,
      window_seconds: 600,
      max_text_chars: 60000,
      asr_available: true,
      tools_available: true,
      gemini_key_configured: true,
    })),
    pick: vi.fn(async () => 'C:/Videos/Entrevista.mp4'),
    create: vi.fn(async () => {
      throw new Error('Não foi possível importar. Tente novamente.');
    }),
  },
}));
beforeEach(() => {
  HTMLDialogElement.prototype.showModal = function () {
    this.setAttribute('open', '');
  };
  HTMLDialogElement.prototype.close = function () {
    this.removeAttribute('open');
    this.dispatchEvent(new Event('close'));
  };
});

it('preserves picked file and suggested name after a recoverable creation failure', async () => {
  const w = mount(App, { attachTo: document.body });
  try {
    await flushPromises();
    await w.get('.new-project-action').trigger('click');
    await flushPromises();
    await w.get('.file-drop button').trigger('click');
    await flushPromises();
    await w.get('dialog[open] form').trigger('submit');
    await flushPromises();
    expect(w.get('dialog[open] [role=alert]').text()).toContain('Tente novamente');
    expect(w.get('dialog[open] .project-name-field input').element.value).toBe('Entrevista');
    expect(w.get('dialog[open]').text()).toContain('Entrevista.mp4');
  } finally {
    w.unmount();
  }
});

it('submits a supported URL exactly once while pending', async () => {
  let reject!: (error: Error) => void;
  vi.mocked(api.create).mockImplementationOnce(
    () =>
      new Promise((_resolve, fail) => {
        reject = fail;
      })
  );
  const before = vi.mocked(api.create).mock.calls.length;
  const w = mount(App, { attachTo: document.body });
  try {
    await flushPromises();
    await w.get('.new-project-action').trigger('click');
    await flushPromises();
    await w.findAll('dialog[open] [role=radio]')[1].trigger('click');
    await w.get('dialog[open] input[type=url]').setValue('https://youtu.be/fixture');
    await w.get('dialog[open] .project-name-field input').setValue('URL de teste');
    await w.get('dialog[open] form').trigger('submit');
    await w.get('dialog[open] form').trigger('submit');
    expect(api.create).toHaveBeenCalledTimes(before + 1);
    expect(api.create).toHaveBeenLastCalledWith('URL de teste', 'https://youtu.be/fixture', {
      automatic: true,
    });
    reject(new Error('Falha recuperável'));
    await flushPromises();
    expect(w.get('dialog[open] input[type=url]').element.value).toBe('https://youtu.be/fixture');
  } finally {
    w.unmount();
  }
});

it.each([
  { sourceInput: 'https://youtube.com.evil.test/watch?v=fixture', toolsAvailable: true },
  { sourceInput: 'https://youtu.be/fixture', toolsAvailable: false },
])(
  'blocks invalid URLs or missing video dependencies: $toolsAvailable $sourceInput',
  async ({ sourceInput, toolsAvailable }) => {
    const w = mount(NewProjectDialog, {
      props: {
        modelValue: true,
        name: 'Teste',
        sourceInput,
        sourceKind: 'url',
        busy: false,
        setupReady: toolsAvailable,
        toolsAvailable,
        configSummary: 'Whisper local · Gemini',
      },
    });
    try {
      expect(w.get('[type=submit]').attributes('disabled')).toBeDefined();
      await w.get('form').trigger('submit');
      expect(w.emitted('submit')).toBeUndefined();
    } finally {
      w.unmount();
    }
  }
);

it('imports a project through the existing App orchestration', async () => {
  const project = {
    id: 'imported',
    name: 'Importado',
    title: 'Projeto importado',
    word_count: 0,
    warnings: [],
    status: 'imported',
    has_transcript: false,
    is_manual: false,
    source: null,
  };
  Object.assign(api, {
    importProject: vi.fn(async () => project),
    project: vi.fn(async () => project),
    revisions: vi.fn(async () => []),
    analysis: vi.fn(async () => null),
    selection: vi.fn(async () => null),
  });
  const w = mount(App, { attachTo: document.body });
  try {
    await flushPromises();
    await w.get('.header-import-action').trigger('click');
    await flushPromises();
    expect(w.get('h1').text()).toBe('Projeto importado');
    expect(api.importProject).toHaveBeenCalledWith('C:/Videos/Entrevista.mp4');
  } finally {
    w.unmount();
  }
});

it('switches source with arrow keys without losing the project name', async () => {
  const w = mount(NewProjectDialog, {
    attachTo: document.body,
    props: {
      modelValue: true,
      name: 'Nome preservado',
      sourceInput: '',
      sourceKind: 'file',
      busy: false,
      setupReady: true,
      toolsAvailable: true,
      configSummary: 'Whisper local',
    },
  });
  try {
    await w.get('.source-switch').trigger('keydown', { key: 'ArrowRight' });
    expect(w.find('input[type=url]').exists()).toBe(true);
    expect(document.activeElement?.getAttribute('aria-checked')).toBe('true');
    expect(w.get('.project-name-field input').element.value).toBe('Nome preservado');
  } finally {
    w.unmount();
  }
});

it('does not describe a pending file picker as project creation', async () => {
  let finishPicker!: (value: string) => void;
  vi.mocked(api.pick).mockImplementationOnce(
    () =>
      new Promise(resolve => {
        finishPicker = resolve;
      })
  );
  const w = mount(App, { attachTo: document.body });
  try {
    await flushPromises();
    await w.get('.new-project-action').trigger('click');
    await flushPromises();
    await w.get('.file-drop button').trigger('click');
    await flushPromises();
    expect(w.get('dialog[open] [type=submit]').text()).not.toContain('Criando');
    expect(w.get('dialog[open] [type=submit]').attributes('disabled')).toBeDefined();
    finishPicker('C:/Videos/Escolhido.mp4');
    await flushPromises();
  } finally {
    w.unmount();
  }
});

it('cancels the native dialog and reopens it without leaving a stale open state', async () => {
  const w = mount(App, { attachTo: document.body });
  try {
    await flushPromises();
    await w.get('.new-project-action').trigger('click');
    await flushPromises();
    const cancel = new Event('cancel', { cancelable: true });
    w.get('dialog[open]').element.dispatchEvent(cancel);
    await flushPromises();
    expect(cancel.defaultPrevented).toBe(true);
    expect(w.find('dialog[open]').exists()).toBe(false);
    await w.get('.new-project-action').trigger('click');
    await flushPromises();
    expect(w.find('dialog[open]').exists()).toBe(true);
    (w.get('dialog[open]').element as HTMLDialogElement).close();
    await flushPromises();
    expect(w.getComponent(NewProjectDialog).props('modelValue')).toBe(false);
  } finally {
    w.unmount();
  }
});

it.each([
  { busy: true, picking: false },
  { busy: false, picking: true },
])('prevents native Escape cancellation while an operation is pending: %o', async pending => {
  const w = mount(NewProjectDialog, {
    attachTo: document.body,
    props: {
      modelValue: true,
      name: 'Teste',
      sourceInput: '/fixture.mp4',
      sourceKind: 'file',
      setupReady: true,
      toolsAvailable: true,
      configSummary: 'Local',
      ...pending,
    },
  });
  try {
    const cancel = new Event('cancel', { cancelable: true });
    w.get('dialog').element.dispatchEvent(cancel);
    await flushPromises();
    expect(cancel.defaultPrevented).toBe(true);
    expect(w.emitted('update:modelValue')).toBeUndefined();
    expect(w.get('dialog').attributes('open')).toBeDefined();
  } finally {
    w.unmount();
  }
});

it('creates without automatic preparation when video tools exist but ASR and credentials do not', async () => {
  const readyConfig = await api.config();
  vi.mocked(api.config).mockResolvedValueOnce({
    ...readyConfig,
    tools_available: true,
    asr_available: false,
    gemini_key_configured: false,
  });
  const w = mount(App, { attachTo: document.body });
  try {
    await flushPromises();
    w.getComponent(OnboardingModal).vm.$emit('close');
    await flushPromises();
    await w.get('.new-project-action').trigger('click');
    await flushPromises();
    await w.get('.file-drop button').trigger('click');
    await flushPromises();
    expect(w.get('dialog[open]').text()).toContain('sem preparação automática');
    await w.get('dialog[open] form').trigger('submit');
    await flushPromises();
    expect(api.create).toHaveBeenLastCalledWith('Entrevista', 'C:/Videos/Entrevista.mp4', {
      automatic: false,
    });
  } finally {
    w.unmount();
  }
});
