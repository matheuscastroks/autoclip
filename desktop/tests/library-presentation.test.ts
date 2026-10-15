import { mount } from '@vue/test-utils';
import { expect, it } from 'vitest';
import ProjectLibrary from '../src/components/ProjectLibrary.vue';
import AppSelect from '../src/components/AppSelect.vue';
import type { Project } from '../src/types';

const project = {
  id: 'p',
  name: 'Entrevista',
  title: 'Título extenso '.repeat(20),
  status: 'failed',
  duration_us: 30000000,
  has_transcript: true,
  word_count: 100,
  updated_at: 0,
  summary: { proposed: 4, selected: 2, generated: 1, stage: 'analyze' },
} as Project;

it('shows failure instead of a stale pipeline stage in both list and grid', async () => {
  const w = mount(ProjectLibrary, { props: { projects: [project], busy: false } });
  try {
    expect(w.get('[data-status=failed]').text()).toBe('Precisa de atenção');
    await w.get('[aria-label="Grade de Mídia"]').trigger('click');
    expect(w.get('[data-status=failed]').text()).toBe('Precisa de atenção');
    expect(w.text()).not.toContain('1 prontos');
  } finally {
    w.unmount();
  }
});

it('falls back on broken thumbnails and does not invent unavailable counts', async () => {
  const w = mount(ProjectLibrary, {
    props: {
      projects: [{ ...project, summary: undefined }],
      busy: false,
      covers: { p: '/broken.jpg' },
    },
  });
  try {
    await w.get('img').trigger('error');
    expect(w.find('img').exists()).toBe(false);
    expect(w.text()).toContain('Resumo indisponível');
    expect(w.text()).not.toContain('0 gerados');
    await w.setProps({ covers: { p: '/new.jpg' } });
    expect(w.get('img').attributes('src')).toBe('/new.jpg');
  } finally {
    w.unmount();
  }
});

it('does not open a project when deleting with keyboard and protects active projects', async () => {
  const w = mount(ProjectLibrary, { props: { projects: [project], busy: false } });
  try {
    await w.get('[data-action=delete-project]').trigger('keydown', { key: 'Enter' });
    expect(w.emitted('open')).toBeUndefined();
    await w.get('[data-action=delete-project]').trigger('click');
    expect(w.emitted('delete')?.[0]).toEqual(['p']);
    await w.setProps({ activeProjects: ['p'] });
    expect(w.get('[data-action=delete-project]').attributes('disabled')).toBeDefined();
  } finally {
    w.unmount();
  }
});

it('combines search, state filtering and ordering without resetting them on view change', async () => {
  const w = mount(ProjectLibrary, {
    props: {
      busy: false,
      projects: [
        { ...project, id: 'b', title: 'Entrevista Beta', updated_at: 3 },
        { ...project, id: 'a', title: 'Entrevista Alfa', updated_at: 1 },
        { ...project, id: 'c', title: 'Entrevista Completa', status: 'completed', updated_at: 2 },
      ],
    },
  });
  try {
    await w.get('[aria-label="Buscar projetos"]').setValue('Entrevista');
    w.findAllComponents(AppSelect)[0].vm.$emit('update:modelValue', 'failed');
    w.findAllComponents(AppSelect)[1].vm.$emit('update:modelValue', 'name');
    await w.vm.$nextTick();
    expect(w.findAll('[data-project-id]').map(row => row.attributes('data-project-id'))).toEqual([
      'a',
      'b',
    ]);
    await w.get('[aria-label="Grade de Mídia"]').trigger('click');
    expect(w.findAll('[data-project-id]').map(row => row.attributes('data-project-id'))).toEqual([
      'a',
      'b',
    ]);
  } finally {
    w.unmount();
  }
});
