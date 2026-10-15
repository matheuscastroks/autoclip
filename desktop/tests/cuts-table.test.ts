import { mount, flushPromises } from '@vue/test-utils';
import { it, expect } from 'vitest';
import ReviewPanel from '../src/components/ReviewPanel.vue';
import type { Job } from '../src/types';
it('shows interrupted final work without hiding its valid preview', () => {
  const w = mount(ReviewPanel, {
    props: {
      manual: false,
      mediaUrl: '',
      sourceUrl: '',
      revisions: [
        {
          revision_id: 'r',
          candidate_id: 'c',
          title: 'Corte',
          technical_pass: false,
          final_state: 'not_generated',
          review_status: 'needs_review',
          warnings: [],
          preview: { state: 'available', asset: 'preview-r' },
        },
      ],
      jobs: [
        {
          id: 'j',
          created_at: '2026-10-15T10:00:00Z',
          operation: 'render_final',
          status: 'interrupted',
          progress: {
            items: [
              { revision_id: 'r', candidate_id: 'c', state: 'pending', phase: 'render_final' },
            ],
          },
        } as Job,
      ],
    },
  });
  try {
    expect(w.get('tbody tr.clip-item').text()).toContain('Final interrompida');
    expect(w.get('tbody tr.clip-item').text()).toContain('Prévia disponível');
  } finally {
    w.unmount();
  }
});
it('separates final availability from editorial status and never exports an invalidated final', async () => {
  const w = mount(ReviewPanel, {
    props: {
      manual: false,
      mediaUrl: '',
      sourceUrl: '',
      revisions: [
        {
          revision_id: 'r',
          title: 'Corte',
          technical_pass: true,
          final_state: 'invalid',
          review_status: 'approved',
          warnings: [],
        },
      ],
    },
  });
  try {
    expect((w.get('.cuts-table-heading button').element as HTMLButtonElement).disabled).toBe(true);
    await w.get('input[aria-label="Selecionar corte: Corte"]').setValue(true);
    const bulkExport = w
      .findAll('.bulk-actions button')
      .find(b => b.text() === 'Exportar selecionados')!;
    expect((bulkExport.element as HTMLButtonElement).disabled).toBe(true);
    await w
      .findAll('.cuts-filter-chip')
      .find(b => b.text() === 'Aprovados')!
      .trigger('click');
    expect(w.find('tbody tr.clip-item').exists()).toBe(false);
    await w
      .findAll('.cuts-filter-chip')
      .find(b => b.text() === 'Todos')!
      .trigger('click');
    await w.setProps({
      revisions: [
        { ...w.props('revisions')[0], final_state: 'available', review_status: 'needs_review' },
      ],
    });
    expect(w.get('tbody tr.clip-item').text()).toContain('Final disponível');
    expect(w.get('[data-editorial-status]').text()).toContain('Revisão editorial pendente');
  } finally {
    w.unmount();
  }
});
it('selects a table row with the keyboard without changing bulk selection', async () => {
  const revisions = ['a', 'b'].map(id => ({
    revision_id: id,
    title: 'Corte ' + id,
    rationale: 'Justificativa ' + id,
    technical_pass: true,
    review_status: 'needs_review',
    duration_us: 60000000,
    start_us: 0,
    end_us: 60000000,
    warnings: [],
    content_hash: id,
  }));
  const w = mount(ReviewPanel, {
    props: { manual: false, mediaUrl: '/a.mp4', sourceUrl: '', revisions },
  });
  for (const check of w.findAll('input[type=checkbox]')) await check.setValue(true);
  await w.get('select[aria-label="Ordenar cortes"]').setValue('title');
  await w.findAll('tbody tr')[1].trigger('keydown', { key: 'Enter' });
  await flushPromises();
  expect(w.emitted('select')?.at(-1)).toEqual(['b']);
  expect(w.get('.clip-drawer-heading .preview-label').text()).toBe('Corte b');
  expect(w.get('tbody tr.selected').attributes('aria-selected')).toBe('true');
  expect(w.find('[data-action=approve]').exists()).toBe(false);
  expect(w.find('.cuts-player-rail').exists()).toBe(false);
  expect(w.find('.clip-preview video').exists()).toBe(true);
  w.unmount();
});

it('shows only editorially approved clips as ready and blocks pending bulk export', async () => {
  const revisions = [
    {
      revision_id: 'approved',
      title: 'Aprovado',
      technical_pass: true,
      review_status: 'approved',
      warnings: [],
    },
    {
      revision_id: 'pending',
      title: 'Pendente',
      technical_pass: true,
      review_status: 'needs_review',
      warnings: [],
    },
  ];
  const w = mount(ReviewPanel, {
    props: { manual: false, mediaUrl: '', sourceUrl: '', revisions },
  });
  expect((w.get('.cuts-table-heading button').element as HTMLButtonElement).disabled).toBe(false);
  await w.get('input[aria-label="Selecionar todos os cortes visíveis"]').setValue(true);
  const exportSelected = w
    .get('.bulk-actions')
    .findAll('button')
    .find(button => button.text().includes('Exportar selecionados'))!;
  expect((exportSelected.element as HTMLButtonElement).disabled).toBe(true);
  await w
    .findAll('.cuts-filter-chip')
    .find(button => button.text() === 'Aprovados')!
    .trigger('click');
  expect(w.findAll('tbody tr.clip-item')).toHaveLength(1);
  expect(w.get('tbody tr.clip-item').text()).toContain('Aprovado');
  w.unmount();
});

it('requires human confirmation of each editorial criterion before approval', async () => {
  const w = mount(ReviewPanel, {
    props: {
      manual: false,
      mediaUrl: '/preview.mp4',
      sourceUrl: '/source.mp4',
      revisions: [
        {
          revision_id: 'review',
          title: 'Corte',
          technical_pass: true,
          review_status: 'needs_review',
          content_hash: 'a'.repeat(64),
          warnings: [],
        },
      ],
    },
  });
  await w.get('.clip-item').trigger('click');
  await flushPromises();
  const approve = w.get('[data-action=editorial-approve]');
  expect(w.get('a[download]').text()).toContain('final técnico');
  expect((approve.element as HTMLButtonElement).disabled).toBe(true);
  const checks = w.findAll('.editorial-checklist input[type=checkbox]');
  expect(checks).toHaveLength(5);
  for (const check of checks) await check.setValue(true);
  expect((approve.element as HTMLButtonElement).disabled).toBe(false);
  await approve.trigger('click');
  expect(w.emitted('decision')?.[0]?.[0]).toMatchObject({
    decision: 'approved',
    checks: {
      completeness: true,
      context: true,
      qualifications: true,
      words_and_boundaries: true,
      audiovisual: true,
    },
  });
  await w.setProps({ revisions: [{ ...w.props('revisions')[0], content_hash: 'b'.repeat(64) }] });
  expect((approve.element as HTMLButtonElement).disabled).toBe(true);
  expect(
    w
      .findAll('.editorial-checklist input')
      .every(input => !(input.element as HTMLInputElement).checked)
  ).toBe(true);
  w.unmount();
});

it('includes outdated editorial decisions in the review queue', async () => {
  const w = mount(ReviewPanel, {
    props: {
      manual: false,
      mediaUrl: '',
      sourceUrl: '',
      revisions: [
        {
          revision_id: 'stale',
          title: 'Revisar novamente',
          technical_pass: true,
          review_status: 'stale_review',
          warnings: [],
        },
      ],
    },
  });
  await w
    .findAll('.cuts-filter-chip')
    .find(button => button.text() === 'Para revisar')!
    .trigger('click');
  expect(w.get('tbody tr.clip-item').text()).toContain('Revisar novamente');
  expect((w.get('.cuts-table-heading button').element as HTMLButtonElement).disabled).toBe(true);
  w.unmount();
});
