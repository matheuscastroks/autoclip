import { mount, flushPromises } from '@vue/test-utils';
import { beforeEach, afterEach, describe, it, expect, vi } from 'vitest';
import ClipPreviewDrawer from '../src/components/ClipPreviewDrawer.vue';
import type { Revision } from '../src/types';

const preview = {
  revision_id: 'r',
  title: 'Corte de teste',
  duration_us: 60_000_000,
  technical_pass: false,
  review_status: 'needs_review',
  warnings: [],
  preview: { state: 'available', asset: 'preview-r' },
  final_state: 'not_generated',
  can_render_final: true,
} as Revision;
beforeEach(() => {
  vi.spyOn(HTMLMediaElement.prototype, 'pause').mockImplementation(() => {});
  vi.spyOn(HTMLMediaElement.prototype, 'load').mockImplementation(() => {});
});
afterEach(() => vi.restoreAllMocks());
function open(revision = preview, loadMedia = vi.fn().mockResolvedValue('/preview.mp4')) {
  return mount(ClipPreviewDrawer, {
    props: { modelValue: true, revision, loadMedia },
    global: { stubs: { teleport: true } },
  });
}
describe('clip preview drawer', () => {
  it('keeps final details collapsed and blocks export when technical validation no longer passes', async () => {
    const w = open({
      ...preview,
      final_state: 'available',
      technical_pass: false,
      review_status: 'approved',
    });
    try {
      await flushPromises();
      expect(
        w.findAll('.clip-drawer-actions button').some(b => b.text() === 'Exportar aprovados')
      ).toBe(false);
      const details = w.findAll('.clip-inspection-details details')[0];
      expect((details.element as HTMLDetailsElement).open).toBe(false);
    } finally {
      w.unmount();
    }
  });
  it('invalidates a pending ticket when the real Drawer close button is used', async () => {
    let resolve: (url: string) => void = () => {};
    const w = open(
      preview,
      vi.fn().mockImplementation(() => new Promise(r => (resolve = r)))
    );
    await flushPromises();
    await w.get('.el-drawer__close-btn').trigger('click');
    resolve('/late.mp4');
    await flushPromises();
    expect(w.find('video').exists()).toBe(false);
    expect(w.emitted('update:modelValue')?.at(-1)).toEqual([false]);
    w.unmount();
  });
  it('loads only the preview on demand and never offers editorial approval', async () => {
    const load = vi.fn().mockResolvedValue('/preview.mp4');
    const w = open(preview, load);
    await flushPromises();
    expect(load).toHaveBeenCalledWith('preview-r');
    expect(w.get('video').attributes('src')).toBe('/preview.mp4');
    expect(w.find('[data-action=editorial-approve]').exists()).toBe(false);
    await w.get('[data-action=render-final]').trigger('click');
    expect(w.emitted('renderFinal')).toEqual([['r']]);
    expect(w.emitted('decision')).toBeUndefined();
    await w.setProps({ modelValue: false });
    expect(w.find('video').exists()).toBe(false);
    expect(HTMLMediaElement.prototype.pause).toHaveBeenCalled();
    w.unmount();
  });
  it('switches versions and requires five confirmations for the exact final fingerprint', async () => {
    const load = vi.fn().mockImplementation(async asset => '/media/' + asset);
    const w = open(
      { ...preview, final_state: 'available', technical_pass: true, content_hash: 'hash' },
      load
    );
    await flushPromises();
    await w.get('[data-version=final]').trigger('click');
    await flushPromises();
    expect(w.get('video').attributes('src')).toBe('/media/r');
    const approve = w.get('[data-action=editorial-approve]');
    expect((approve.element as HTMLButtonElement).disabled).toBe(true);
    for (const input of w.findAll('.editorial-checklist input')) await input.setValue(true);
    await approve.trigger('click');
    expect(w.emitted('decision')?.[0][0]).toMatchObject({
      revision_id: 'r',
      content_hash: 'hash',
      decision: 'approved',
    });
    await w.setProps({ revision: { ...w.props('revision')!, content_hash: 'changed' } });
    expect((approve.element as HTMLButtonElement).disabled).toBe(true);
    w.unmount();
  });
  it('ignores stale ticket responses and allows retry after a load error', async () => {
    let resolve: (url: string) => void = () => {};
    const load = vi
      .fn()
      .mockImplementationOnce(() => new Promise(r => (resolve = r)))
      .mockRejectedValueOnce(new Error('Mídia indisponível'))
      .mockResolvedValue('/new.mp4');
    const w = open(preview, load);
    await w.setProps({
      revision: {
        ...preview,
        revision_id: 'new',
        preview: { state: 'available', asset: 'preview-new' },
      },
    });
    await flushPromises();
    resolve('/stale.mp4');
    await flushPromises();
    expect(w.find('video').exists()).toBe(false);
    await w.get('[data-action=retry-media]').trigger('click');
    await flushPromises();
    expect(w.get('video').attributes('src')).toBe('/new.mp4');
    w.unmount();
  });
});
