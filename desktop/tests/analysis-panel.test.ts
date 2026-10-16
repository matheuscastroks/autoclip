import { mount, flushPromises } from '@vue/test-utils';
import { it, expect, vi } from 'vitest';
import AnalysisPanel from '../src/components/AnalysisPanel.vue';
const proposal = {
  candidate_id: 'one',
  topic_ids: ['t'],
  group_id: 'tema',
  title: 'O argumento completo',
  rationale: 'Mantém a conclusão.',
  start_us: 1000000,
  end_us: 61000000,
  duration_us: 60000000,
  start_word_id: 'w1',
  end_word_id: 'w2',
  evidence_word_ids: ['w1'],
  editorial: { completeness: 'yes' },
  warnings: [],
  eligible: true,
  reasons: [],
  text: 'Fala original.',
  context_before: 'Antes.',
  context_after: 'Depois.',
};
const view = {
  schema_version: '1.0',
  state: 'completed',
  job_id: null,
  analysis_hash: 'a'.repeat(64),
  model: 'fixture',
  completed_windows: 2,
  total_windows: 2,
  topic_groups: [
    {
      id: 'tema',
      label: 'Tema',
      topic_ids: ['t'],
      summaries: ['Resumo'],
      evidence_word_ids: ['w1'],
    },
  ],
  proposals: [
    proposal,
    {
      ...proposal,
      candidate_id: 'two',
      eligible: false,
      reasons: ['editorial flags require review'],
    },
  ],
};
it('loads inspection only on explicit opening and checkbox selection never opens it', async () => {
  const w = mount(AnalysisPanel, {
    props: { analysis: view, selection: null, jobs: [], sourceUrl: '/source.mp4', busy: false },
    global: { stubs: { teleport: true } },
  });
  try {
    expect(w.find('video').exists()).toBe(false);
    await w.findAll('input[type=checkbox]')[0].setValue(true);
    expect(w.find('[role=dialog]').isVisible()).toBe(false);
    expect(w.emitted('selection')?.[0]?.[0]).toMatchObject({ candidate_ids: ['one'] });
    await w.get('.proposal-open').trigger('click');
    await flushPromises();
    expect(w.get('[role=dialog]').attributes('aria-modal')).toBe('true');
    expect(w.get('video').attributes('src')).toBe('/source.mp4');
    expect(w.findAll('[data-action=generate-selected]')).toHaveLength(1);
    expect(w.emitted('selection')).toHaveLength(1);
    const video = w.get('video').element as HTMLVideoElement;
    await w.get('.el-drawer__close-btn').trigger('click');
    await flushPromises();
    expect(video.getAttribute('src')).toBeNull();
    expect(w.find('video').exists()).toBe(false);
    expect((w.findAll('input[type=checkbox]')[0].element as HTMLInputElement).checked).toBe(true);
  } finally {
    w.unmount();
  }
});
it('bounds original playback to the proposal and its optional 15-second context', async () => {
  const play = vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue();
  const w = mount(AnalysisPanel, {
    props: { analysis: view, selection: null, jobs: [], sourceUrl: '/source.mp4', busy: false },
    global: { stubs: { teleport: true } },
  });
  try {
    await w.get('.proposal-open').trigger('click');
    await flushPromises();
    const video = w.get('video').element as HTMLVideoElement;
    await w.get('[data-action=play-proposal]').trigger('click');
    expect(video.currentTime).toBe(1);
    video.currentTime = 62;
    await w.get('video').trigger('timeupdate');
    expect(HTMLMediaElement.prototype.pause).toHaveBeenCalled();
    await w.get('[data-action=play-context]').trigger('click');
    expect(video.currentTime).toBe(0);
    expect(play).toHaveBeenCalledTimes(2);
  } finally {
    w.unmount();
    play.mockRestore();
  }
});
it('explains a damaged saved analysis and blocks generation', () => {
  const diagnostic = 'Arquivo analysis.json inválido ou corrompido. Os dados foram preservados.';
  const w = mount(AnalysisPanel, {
    props: {
      analysis: { ...view, state: 'invalid', diagnostic, analysis_hash: null, proposals: [] },
      selection: null,
      jobs: [],
      sourceUrl: '',
      busy: false,
    },
  });
  expect(w.get('[role=alert]').text()).toBe(diagnostic);
  expect(w.get('[data-action=generate-selected]').attributes('disabled')).toBeDefined();
  w.unmount();
});
it('selects and removes the inspected proposal through the final step', async () => {
  const w = mount(AnalysisPanel, {
    props: { analysis: view, selection: null, jobs: [], sourceUrl: '', busy: false },
  });
  await w.get('.proposal-open').trigger('click');
  await flushPromises();
  await w.get('[data-action=select-focused]').trigger('click');
  expect(w.emitted('selection')?.[0]?.[0]).toMatchObject({ candidate_ids: ['one'] });
  await w.get('[data-action=select-focused]').trigger('click');
  expect(w.emitted('selection')?.[1]?.[0]).toMatchObject({ candidate_ids: [] });
  w.unmount();
});
it('shows a distinct social opening before generation', async () => {
  const w = mount(AnalysisPanel, {
    props: {
      analysis: {
        ...view,
        proposals: [
          {
            ...proposal,
            title: 'Por que essa ressalva muda tudo',
            opening_text: 'Uma palavra muda o sentido?',
          },
        ],
      },
      selection: null,
      jobs: [],
      sourceUrl: '',
      busy: false,
    },
  });
  await w.get('.proposal-open').trigger('click');
  await flushPromises();
  expect(w.get('.inspector-heading h2').text()).toBe('Por que essa ressalva muda tudo');
  expect(w.get('.opening-copy').text()).toContain('Uma palavra muda o sentido?');
  expect(w.get('.opening-copy').text()).toContain('7 segundos');
  w.unmount();
});
it('generates only explicit eligible proposals and preserves selection on polling', async () => {
  const w = mount(AnalysisPanel, {
    props: { analysis: view, selection: null, jobs: [], sourceUrl: '', busy: false },
  });
  const boxes = w.findAll('input[type=checkbox]');
  expect(boxes[1].attributes('disabled')).toBeDefined();
  await boxes[0].setValue(true);
  await w.setProps({ analysis: structuredClone(view) });
  await w.get('[data-action=generate-selected]').trigger('click');
  expect(w.emitted('generate')?.[0]?.[0]).toEqual({
    analysis_hash: view.analysis_hash,
    candidate_ids: ['one'],
  });
});
it('shows validated partial data without allowing generation', () => {
  const w = mount(AnalysisPanel, {
    props: {
      analysis: { ...view, state: 'partial', analysis_hash: null },
      selection: null,
      jobs: [],
      sourceUrl: '',
      busy: false,
    },
  });
  expect(w.text()).toContain('parcial');
  expect(w.get('[data-action=generate-selected]').attributes('disabled')).toBeDefined();
  expect(w.get('[data-generation-blocked]').text()).toContain('conclusão da análise');
});
it('explains why preview generation is disabled before a proposal is selected', () => {
  const w = mount(AnalysisPanel, {
    props: { analysis: view, selection: null, jobs: [], sourceUrl: '', busy: false },
  });
  expect(w.get('[data-generation-blocked]').text()).toContain('Selecione ao menos uma proposta');
  w.unmount();
});
it('keeps the topic and inspected proposal when partial analysis completes', async () => {
  const other = { ...proposal, candidate_id: 'other', title: 'Outra proposta' };
  const partial = { ...view, state: 'partial', analysis_hash: null, proposals: [proposal, other] };
  const w = mount(AnalysisPanel, {
    props: { analysis: partial, selection: null, jobs: [], sourceUrl: '', busy: false },
  });
  await w.findAll('.topic-list button')[1].trigger('click');
  await w.findAll('.proposal-open')[1].trigger('click');
  await w.setProps({
    analysis: { ...partial, state: 'completed', analysis_hash: view.analysis_hash },
  });
  expect(w.get('.inspector-heading h2').text()).toBe('Outra proposta');
  expect(w.get('.topic-list button.selected').text()).toContain('Tema');
});
it('distinguishes failed analysis from not started and offers no synthetic selection', () => {
  const w = mount(AnalysisPanel, {
    props: {
      analysis: {
        ...view,
        state: 'failed',
        model: null,
        analysis_hash: null,
        proposals: [],
        topic_groups: [],
      },
      selection: null,
      jobs: [],
      sourceUrl: '',
      busy: false,
    },
  });
  expect(w.get('.analysis-heading').text()).toContain('Análise precisa de atenção');
  expect(w.get('.analysis-heading').text()).not.toContain('Análise ainda não iniciada');
  expect(w.find('[data-action=select-focused]').exists()).toBe(false);
  expect(w.get('.proposal-empty').text()).toContain('Os trechos aparecerão aqui');
  expect(w.get('[data-action=generate-selected]').attributes('disabled')).toBeDefined();
  w.unmount();
});
it('disables overlapping proposals and prevents simultaneous selection', async () => {
  const propA = {
    ...proposal,
    candidate_id: 'prop-a',
    title: 'Corte A',
    start_us: 10000000,
    end_us: 50000000,
    duration_us: 40000000,
  };
  const propB = {
    ...proposal,
    candidate_id: 'prop-b',
    title: 'Corte B',
    start_us: 30000000,
    end_us: 70000000,
    duration_us: 40000000,
  };
  const overlapView = { ...view, proposals: [propA, propB] };
  const w = mount(AnalysisPanel, {
    props: { analysis: overlapView, selection: null, jobs: [], sourceUrl: '', busy: false },
  });
  const boxes = w.findAll('input[type=checkbox]');
  expect(boxes[0].attributes('disabled')).toBeUndefined();
  expect(boxes[1].attributes('disabled')).toBeUndefined();
  // Select proposal A
  await boxes[0].setValue(true);
  expect(w.emitted('selection')?.[0]?.[0]).toMatchObject({ candidate_ids: ['prop-a'] });
  // Proposal B should now be disabled because it overlaps with A
  expect(boxes[1].attributes('disabled')).toBeDefined();
  expect(w.text()).toContain('Sobrepõe seleção');
  // Selecting B in inspection panel should also be disabled
  await w.findAll('.proposal-open')[1].trigger('click');
  expect(w.get('[data-action=select-focused]').attributes('disabled')).toBeDefined();
  expect(w.text()).toContain('Este trecho se sobrepõe a um corte já selecionado');
  // Unselect A: B becomes selectable again
  await w.findAll('.proposal-open')[0].trigger('click');
  await w.get('[data-action=select-focused]').trigger('click');
  expect(boxes[1].attributes('disabled')).toBeUndefined();
  w.unmount();
});
it('shows 1-click resume button for partial analysis and emits resume on click', async () => {
  const partialView = {
    ...view,
    state: 'partial',
    analysis_hash: null,
    completed_windows: 1,
    total_windows: 3,
  };
  const w = mount(AnalysisPanel, {
    props: { analysis: partialView, selection: null, jobs: [], sourceUrl: '', busy: false },
  });
  expect(w.find('[data-action=resume-analysis]').exists()).toBe(true);
  expect(w.text()).toContain('Faltam 2 janelas');
  await w.get('[data-action=resume-analysis]').trigger('click');
  expect(w.emitted('resume')).toHaveLength(1);
  w.unmount();
});

it('does not display redundant marketing header texts on complete analysis', () => {
  const w = mount(AnalysisPanel, {
    props: { analysis: view, selection: null, jobs: [], sourceUrl: '', busy: false },
  });
  const headText = w.get('.analysis-heading').text();
  expect(headText).not.toContain('Curadoria Editorial com Inteligência Artificial');
  expect(headText).not.toContain('Temas e propostas');
  expect(headText).not.toContain('janelas validadas');
  w.unmount();
});

it('allows discarding and restoring proposals and deselects discarded items', async () => {
  const w = mount(AnalysisPanel, {
    props: {
      analysis: view,
      selection: {
        schema_version: '1.0',
        analysis_hash: view.analysis_hash,
        candidate_ids: ['one'],
      },
      jobs: [],
      sourceUrl: '',
      busy: false,
    },
  });
  // Initially candidate 'one' is selected
  expect((w.findAll('input[type=checkbox]')[0].element as HTMLInputElement).checked).toBe(true);
  // Discard candidate 'one' via button in proposal card
  await w.get('[data-action=discard-proposal]').trigger('click');
  // Candidate 'one' should be deselected and selection emitted with empty array
  expect(w.emitted('selection')?.slice(-1)[0][0]).toMatchObject({ candidate_ids: [] });
  // Active list should now be empty (proposal 'two' is ineligible, but let's check tabs)
  expect(w.text()).toContain('Descartadas (1)');
  // Switch to discarded filter tab
  const discardedTab = w.findAll('.filter-pill-btn').find(b => b.text().includes('Descartadas'));
  expect(discardedTab).toBeDefined();
  await discardedTab!.trigger('click');
  // Restore proposal
  await w.get('[data-action=restore-proposal]').trigger('click');
  expect(w.text()).toContain('Ativas (2)');
  w.unmount();
});

it('supports selecting all eligible proposals and clearing selection', async () => {
  const w = mount(AnalysisPanel, {
    props: { analysis: view, selection: null, jobs: [], sourceUrl: '', busy: false },
  });
  await w.get('[data-action=select-all-proposals]').trigger('click');
  expect(w.emitted('selection')?.[0]?.[0]).toMatchObject({ candidate_ids: ['one'] });
  await w.get('[data-action=clear-selection]').trigger('click');
  expect(w.emitted('selection')?.slice(-1)[0][0]).toMatchObject({ candidate_ids: [] });
  w.unmount();
});

it('keeps partially discarded topics navigable with truthful discarded counts', async () => {
  const w = mount(AnalysisPanel, {
    props: { analysis: view, selection: null, jobs: [], sourceUrl: '', busy: false },
  });
  try {
    await w.get('[data-action=discard-proposal]').trigger('click');
    await w.findAll('.filter-pill-btn')[1].trigger('click');
    const topic = w.findAll('.topic-list button').find(b => b.text().includes('Tema'));
    expect(topic).toBeDefined();
    expect(topic!.text()).toContain('1');
    await topic!.trigger('click');
    expect(w.findAll('.proposal-item')).toHaveLength(1);
    await w.get('[data-action=restore-proposal]').trigger('click');
    expect(w.get('.proposal-empty').text()).toContain('Nenhuma proposta');
  } finally {
    w.unmount();
  }
});

it('invalidates open inspection and local selection when a completed analysis hash changes', async () => {
  const w = mount(AnalysisPanel, {
    props: { analysis: view, selection: null, jobs: [], sourceUrl: '/original.mp4', busy: false },
    global: { stubs: { teleport: true } },
  });
  try {
    await w.findAll('input[type=checkbox]')[0].setValue(true);
    await w.get('.proposal-open').trigger('click');
    await flushPromises();
    expect(w.find('video').exists()).toBe(true);
    await w.setProps({ analysis: { ...view, analysis_hash: 'b'.repeat(64) } });
    await flushPromises();
    expect(w.find('video').exists()).toBe(false);
    expect((w.findAll('input[type=checkbox]')[0].element as HTMLInputElement).checked).toBe(false);
  } finally {
    w.unmount();
  }
});

it('retains hash-bound selection and discarded proposals when completed job history disappears', async () => {
  localStorage.clear();
  const w = mount(AnalysisPanel, {
    props: {
      analysis: { ...view, job_id: 'completed-job' },
      selection: null,
      jobs: [],
      sourceUrl: '',
      busy: false,
    },
  });
  try {
    await w.findAll('input[type=checkbox]')[0].setValue(true);
    await w.findAll('[data-action=discard-proposal]')[1].trigger('click');
    expect(w.text()).toContain('Descartadas (1)');
    await w.setProps({ analysis: { ...view, job_id: null } });
    expect((w.findAll('input[type=checkbox]')[0].element as HTMLInputElement).checked).toBe(true);
    expect(w.text()).toContain('Descartadas (1)');
    await w.get('[data-action=generate-selected]').trigger('click');
    expect(w.emitted('generate')?.[0]).toEqual([
      { analysis_hash: view.analysis_hash, candidate_ids: ['one'] },
    ]);
  } finally {
    w.unmount();
    localStorage.clear();
  }
});
