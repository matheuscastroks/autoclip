import { mount, flushPromises } from '@vue/test-utils';
import { describe, it, expect } from 'vitest';
import ReviewPanel from '../src/components/ReviewPanel.vue';
import type { Job, Revision } from '../src/types';

describe('cut deletion during processing', () => {
  it('selects visible rows without changing preview and emits exact batch ids', async () => {
    const wrapper = mount(ReviewPanel, {
      props: {
        revisions: ['a', 'b'].map(
          id =>
            ({
              revision_id: id,
              title: id,
              technical_pass: true,
              warnings: [],
              review_status: 'approved',
            }) as unknown as Revision
        ),
        manual: false,
        mediaUrl: '',
        sourceUrl: '',
        jobs: [],
      },
    });
    await wrapper.get('input[aria-label="Selecionar todos os cortes visíveis"]').setValue(true);
    expect(wrapper.findAll('.bulk-check input:checked')).toHaveLength(3);
    await wrapper.get('.bulk-actions').findAll('button')[1].trigger('click');
    expect([...(wrapper.emitted('bulkExport')?.[0][0] as string[])].sort()).toEqual(['a', 'b']);
    wrapper.unmount();
  });
  for (const operation of ['analyze', 'transcribe', 'render', 'export', 'prepare', 'import']) {
    it(operation, async () => {
      const blocked = !['analyze', 'transcribe'].includes(operation);
      const wrapper = mount(ReviewPanel, {
        props: {
          revisions: [
            {
              revision_id: 'cut',
              title: 'Corte',
              technical_pass: true,
              warnings: [],
              review_status: 'needs_review',
            } as unknown as Revision,
          ],
          manual: false,
          mediaUrl: '',
          sourceUrl: '',
          processing: true,
          jobs: [{ id: 'job', operation, status: 'running' } as Job],
        },
      });
      await wrapper.get('.clip-item').trigger('click');
      await flushPromises();
      expect(
        (wrapper.get('[data-action="delete-clip"]').element as HTMLButtonElement).disabled
      ).toBe(blocked);
      expect(wrapper.find('#delete-blocked-reason').exists()).toBe(blocked);
      wrapper.unmount();
    });
  }
});
