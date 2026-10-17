import { mount } from '@vue/test-utils';
import { expect, it, vi } from 'vitest';
import PipelinePanel from '../src/components/PipelinePanel.vue';
import type { AnalysisView, Job, Project } from '../src/types';

const project = {
  id: 'p',
  name: 'Entrevista',
  title: 'Entrevista',
  status: 'analyzed',
  source: { local_path: '/fixture', sha256: 'a'.repeat(64) },
  has_transcript: true,
  has_analysis: true,
  is_manual: false,
  word_count: 100,
  warnings: [],
} as Project;
const job = {
  id: 'current',
  project_id: 'p',
  operation: 'render_final',
  status: 'running',
  created_at: '2026-10-15T14:00:00Z',
  requests_used: 0,
  events: [],
  progress: { stage: 'render', steps: {}, total_items: 3, completed_items: 1 },
} as Job;
const analysis = {
  state: 'completed',
  proposals: [],
  topic_groups: [],
  completed_windows: 1,
  total_windows: 1,
  analysis_hash: 'a'.repeat(64),
} as AnalysisView;
function panel(jobs: Job[] = []) {
  return mount(PipelinePanel, {
    props: {
      project,
      jobs,
      busy: false,
      hasCuts: false,
      revisions: [],
      analysis,
      selectedCount: 1,
      selectedCandidateIds: ['c'],
      sourceUrl: '/fixture.mp4',
    },
  });
}

it('prioritizes the current final render over an older failed cut and offers one cancel', async () => {
  const w = panel([
    {
      ...job,
      id: 'old',
      status: 'failed',
      created_at: '2026-10-14T12:00:00Z',
      progress: {
        stage: 'render',
        steps: {},
        items: [{ candidate_id: 'old', state: 'failed', title: 'Falha antiga' }],
      },
    } as Job,
    job,
  ]);
  try {
    expect(w.get('.state-hero-card').text()).toContain('Renderizando versão final');
    expect(w.get('.state-hero-card').text()).not.toContain('Falha antiga');
    const cancel = w.findAll('button').filter(b => b.text() === 'Cancelar');
    expect(cancel).toHaveLength(1);
    await cancel[0].trigger('click');
    expect(w.emitted('cancel')?.[0]).toEqual(['current']);
  } finally {
    w.unmount();
  }
});

it('does not render a video player in preparation panel', async () => {
  const w = panel();
  try {
    expect(w.find('video').exists()).toBe(false);
    expect(w.find('.pipeline-aside').exists()).toBe(true);
  } finally {
    w.unmount();
  }
});

it('blocks preview generation from partial analysis even if project flags are present', async () => {
  const w = panel();
  try {
    await w.setProps({ analysis: { ...analysis, state: 'partial' } });
    const generate = w.findAll('button').filter(b => b.text().includes('Gerar prévias rápidas'));
    expect(generate.length).toBeGreaterThan(0);
    expect(generate.every(b => b.attributes('disabled') !== undefined)).toBe(true);
  } finally {
    w.unmount();
  }
});

it('provides explicit interrupted analysis recovery without hiding its cause', async () => {
  const w = panel([
    {
      ...job,
      operation: 'analyze',
      status: 'interrupted',
      error: { code: 'INTERRUPTED', message: 'A sessão foi interrompida.' },
    },
  ]);
  try {
    expect(w.get('.state-hero-card').text()).toContain('interrompida');
    await w.get('.hero-primary-btn').trigger('click');
    expect(w.emitted('resume')?.[0]).toEqual(['current']);
  } finally {
    w.unmount();
  }
});

it.each([
  ['preview', 'render', 'Gerando prévias rápidas'],
  ['render_final', 'verify', 'Validando versão final'],
])('distinguishes %s processing from final validation', async (operation, stage, title) => {
  const w = panel([
    {
      ...job,
      operation,
      stage: operation,
      progress: { stage: operation, phase: stage, steps: {} },
    } as Job,
  ]);
  try {
    expect(w.get('.state-hero-card h2').text()).toBe(title);
    expect(w.get('.state-hero-card progress').attributes('value')).toBeUndefined();
    expect(w.emitted('generate')).toBeUndefined();
    expect(w.emitted('export')).toBeUndefined();
  } finally {
    w.unmount();
  }
});

it('reports real completed-item counts instead of inventing overall progress', () => {
  const w = panel([job]);
  try {
    expect(w.get('.state-hero-card progress').attributes('value')).toBe('1');
    expect(w.get('.state-hero-card progress').attributes('max')).toBe('3');
    expect(w.get('.state-hero-card').text()).toContain('1 de 3 cortes processados');
  } finally {
    w.unmount();
  }
});

it('keeps queued work distinct from encoding and disables repeat cancellation', async () => {
  const w = panel([{ ...job, status: 'pending', queue_reason: 'Aguardando outra tarefa.' }]);
  try {
    expect(w.get('.state-hero-card h2').text()).toBe('Versão final na fila');
    expect(w.get('.state-hero-card').text()).toContain('Aguardando outra tarefa');
    expect(w.find('.state-hero-card progress').exists()).toBe(false);
    await w.setProps({ jobs: [{ ...job, status: 'cancelling' }] });
    expect(w.get('.hero-primary-btn').attributes('disabled')).toBeDefined();
  } finally {
    w.unmount();
  }
});

it('does not offer final export for an invalidated final despite retained approval flags', async () => {
  const w = panel();
  try {
    await w.setProps({
      hasCuts: true,
      selectedCount: 0,
      selectedCandidateIds: [],
      revisions: [
        {
          revision_id: 'r',
          technical_pass: true,
          review_status: 'approved',
          final_state: 'invalid',
          warnings: [],
        },
      ],
    });
    expect(w.findAll('button').some(b => b.text() === 'Exportar aprovados')).toBe(false);
  } finally {
    w.unmount();
  }
});

it('recognizes already exported approved finals instead of proposing export again as the next action', async () => {
  const w = panel();
  try {
    await w.setProps({
      hasCuts: true,
      selectedCount: 0,
      selectedCandidateIds: [],
      revisions: [
        {
          revision_id: 'r',
          technical_pass: true,
          review_status: 'approved',
          final_state: 'available',
          exported: true,
          warnings: [],
        },
      ],
    });
    expect(w.get('.state-hero-card h2').text()).toBe('Exportação concluída');
    expect(w.get('.hero-primary-btn').text()).toBe('Abrir cortes');
  } finally {
    w.unmount();
  }
});
