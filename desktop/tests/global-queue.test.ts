import { mount } from '@vue/test-utils';
import { it, expect } from 'vitest';
import GlobalQueueModal from '../src/components/GlobalQueueModal.vue';
import type { Job, Project } from '../src/types';

const dummyProject: Project = {
  id: 'proj-1',
  name: 'projeto-entrevista',
  title: 'Entrevista com Especialista',
  path: '/path/1',
  duration_us: 120000000,
  status: 'processing',
  has_transcript: true,
  word_count: 1500,
  revisions: [],
  has_analysis: true,
  is_manual: false,
  warnings: [],
  created_at: '2026-10-13T01:00:00Z',
  updated_at: 1700000000,
  source: null,
  error: null,
};

const dummyJobs: Job[] = [
  {
    id: 'job-run',
    project_id: 'proj-1',
    operation: 'analyze',
    stage: 'analyze',
    status: 'running',
    created_at: '2026-10-13T02:00:00Z',
    requests_used: 2,
    request_limit: 10,
    events: [],
  },
  {
    id: 'job-pend',
    project_id: 'proj-1',
    operation: 'render',
    stage: 'render',
    status: 'pending',
    created_at: '2026-10-13T02:01:00Z',
    queue_position: 1,
    queue_reason: 'Aguardando término da análise.',
    requests_used: 0,
    request_limit: null,
    events: [],
  },
];

it('renders multi-project active and pending jobs with project title and queue position', async () => {
  const w = mount(GlobalQueueModal, {
    props: { jobs: dummyJobs, projects: [dummyProject], busy: false },
  });
  expect(w.text()).toContain('Fila Global de Tarefas');
  expect(w.text()).toContain('1 em execução · 1 aguardando');
  expect(w.text()).toContain('Entrevista com Especialista');
  expect(w.text()).toContain('Posição 1');
  expect(w.text()).toContain('Aguardando término da análise.');
  w.unmount();
});

it('emits cancel and open events properly', async () => {
  const w = mount(GlobalQueueModal, {
    props: { jobs: dummyJobs, projects: [dummyProject], busy: false },
  });
  // Click project jump
  await w.findAll('.project-jump-btn')[0].trigger('click');
  expect(w.emitted('open')?.[0]).toEqual(['proj-1']);

  // Click cancel on pending job
  const cancelBtns = w.findAll('.cancel-job-btn');
  expect(cancelBtns.length).toBe(2);
  await cancelBtns[1].trigger('click');
  expect(w.emitted('cancel')?.[0]).toEqual(['job-pend']);
  w.unmount();
});

it('blocks only the job being changed while history cleanup is pending', async () => {
  const w = mount(GlobalQueueModal, {
    props: { jobs: dummyJobs, projects: [dummyProject], busy: true, pendingJobIds: ['job-run'] },
  });
  const buttons = w.findAll('.cancel-job-btn');
  expect(buttons[0].attributes('disabled')).toBeDefined();
  expect(buttons[1].attributes('disabled')).toBeUndefined();
  await buttons[1].trigger('click');
  expect(w.emitted('cancel')?.[0]).toEqual(['job-pend']);
  w.unmount();
});

it('allows filtering between active jobs and recent history and emits close', async () => {
  const w = mount(GlobalQueueModal, {
    props: { jobs: dummyJobs, projects: [dummyProject], busy: false },
  });
  const tabs = w.findAll('.queue-tab');
  expect(tabs[0].classes()).toContain('selected');

  await tabs[1].trigger('click');
  expect(tabs[1].classes()).toContain('selected');

  await w.get('.close-btn').trigger('click');
  expect(w.emitted('close')).toHaveLength(1);
  w.unmount();
});
