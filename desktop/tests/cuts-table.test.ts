import { mount } from '@vue/test-utils';
import { it, expect } from 'vitest';
import ReviewPanel from '../src/components/ReviewPanel.vue';
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
  await w.findAll('tbody tr')[1].trigger('keydown', { key: 'Enter' });
  expect(w.emitted('select')?.at(-1)).toEqual(['b']);
  expect(w.get('.clip-information .preview-label').text()).toBe('Corte b');
  expect(w.get('tbody tr.selected').attributes('aria-selected')).toBe('true');
  expect(w.find('[data-action=approve]').exists()).toBe(false);
  expect(w.find('.cuts-player-rail video').exists()).toBe(true);
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
  const approve = w.get('[data-action=editorial-approve]');
  expect(w.get('a[download]').text()).toContain('prévia técnica');
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
