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
