import { mount, flushPromises } from '@vue/test-utils';
import { it, expect, vi } from 'vitest';
import ReviewPanel from '../src/components/ReviewPanel.vue';
import ClipPreviewDrawer from '../src/components/ClipPreviewDrawer.vue';

it('opens a single Drawer only from a row, preserving checkbox selection', async () => {
  const loadMedia = vi.fn().mockResolvedValue('/preview.mp4');
  const w = mount(ReviewPanel, {
    props: {
      manual: false,
      mediaUrl: '',
      sourceUrl: '',
      loadMedia,
      revisions: ['a', 'b'].map(id => ({
        revision_id: id,
        title: id,
        technical_pass: false,
        review_status: 'needs_review',
        warnings: [],
        preview: { state: 'available', asset: 'preview-' + id },
        final_state: 'not_generated',
        can_render_final: true,
      })),
    },
    global: { stubs: { teleport: true, AppSelect: true } },
  });
  expect(w.find('video').exists()).toBe(false);
  expect(loadMedia).not.toHaveBeenCalled();
  await w.get('input[aria-label="Selecionar corte: a"]').setValue(true);
  expect(w.getComponent(ClipPreviewDrawer).props('modelValue')).toBe(false);
  await w
    .findAll('.clip-item')
    .find(row => row.text().startsWith('b'))!
    .trigger('click');
  await flushPromises();
  expect(w.getComponent(ClipPreviewDrawer).props('modelValue')).toBe(true);
  expect(loadMedia).toHaveBeenCalledWith('preview-b');
  expect(
    (w.get('input[aria-label="Selecionar corte: a"]').element as HTMLInputElement).checked
  ).toBe(true);
  expect(w.find('.cuts-player-rail').exists()).toBe(false);
  w.unmount();
});
