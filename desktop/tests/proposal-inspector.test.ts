import { mount, flushPromises } from '@vue/test-utils';
import { it, expect, vi } from 'vitest';
import ProposalInspectorDrawer from '../src/components/analysis/ProposalInspectorDrawer.vue';
import type { Proposal } from '../src/types';
const proposal = {
  candidate_id: 'one',
  title: 'Argumento',
  start_us: 1_000_000,
  end_us: 21_000_000,
  duration_us: 20_000_000,
  eligible: true,
  editorial: { completeness: 'yes' },
  warnings: [],
  reasons: [],
  evidence_word_ids: ['w1'],
  text: 'Texto local.',
  context_before: 'Antes',
  context_after: 'Depois',
  rationale: 'Conclusão preservada.',
} as Proposal;
function open(loadSource: () => Promise<string>) {
  return mount(ProposalInspectorDrawer, {
    props: {
      modelValue: true,
      proposal,
      loadSource,
      sourceUrl: '',
      selected: false,
      discarded: false,
      overlapping: false,
      busy: false,
      analysisComplete: true,
    },
    global: { stubs: { teleport: true } },
  });
}
it('ignores an obsolete media response when the inspected proposal changes', async () => {
  let resolve!: (url: string) => void;
  const load = vi
    .fn()
    .mockImplementationOnce(
      () =>
        new Promise<string>(r => {
          resolve = r;
        })
    )
    .mockResolvedValue('/current.mp4');
  const w = open(load);
  try {
    await w.setProps({ proposal: { ...proposal, candidate_id: 'two' } });
    await flushPromises();
    resolve('/obsolete.mp4');
    await flushPromises();
    expect(w.get('video').attributes('src')).toBe('/current.mp4');
    await w.get('.el-drawer__close-btn').trigger('click');
    await flushPromises();
    expect(w.find('video').exists()).toBe(false);
    expect(w.emitted('update:modelValue')?.at(-1)).toEqual([false]);
  } finally {
    w.unmount();
  }
});
it('retains text and selection after media failure and supports explicit retry', async () => {
  const load = vi
    .fn()
    .mockRejectedValueOnce(new Error('Mídia indisponível'))
    .mockResolvedValue('/recovered.mp4');
  const w = open(load);
  try {
    await flushPromises();
    expect(w.get('[role=alert]').text()).toBe('Mídia indisponível');
    expect(w.text()).toContain('Texto local.');
    await w.get('[data-action=select-focused]').trigger('click');
    expect(w.emitted('toggleSelection')).toHaveLength(1);
    await w.get('[data-action=retry-proposal-media]').trigger('click');
    await flushPromises();
    expect(w.get('video').attributes('src')).toBe('/recovered.mp4');
  } finally {
    w.unmount();
  }
});
