import { mount, flushPromises } from '@vue/test-utils';
import { it, expect, vi } from 'vitest';
import TranscriptPanel from '../src/components/TranscriptPanel.vue';
import { api } from '../src/api';

it('enters edit mode on segment action, saves change and emits update', async () => {
  vi.spyOn(api, 'updateTranscript').mockResolvedValue({
    words: [{ id: 'w1', text: 'Texto', start_us: 1000, end_us: 2000 }],
    segments: [{ id: 's1', text: 'Texto modificado final', start_us: 1000, end_us: 2000 }],
  });

  const transcript = {
    words: [
      { id: 'w1', text: 'Texto', start_us: 1000, end_us: 1500 },
      { id: 'w2', text: 'original', start_us: 1500, end_us: 2000 },
    ],
    segments: [{ id: 's1', text: 'Texto original', start_us: 1000, end_us: 2000 }],
  };

  const w = mount(TranscriptPanel, {
    props: {
      projectId: 'p1',
      transcript,
      sourceUrl: '/source.mp4',
      wordCount: 2,
    },
  });

  // Verify edit button exists on row
  const editBtn = w.get('[data-action=edit-segment]');
  await editBtn.trigger('click');

  // Verify textarea appears with current text
  const textarea = w.get('textarea.segment-editor-input');
  expect((textarea.element as HTMLTextAreaElement).value).toBe('Texto original');

  // Modify text
  await textarea.setValue('Texto modificado');

  // Cancel with Esc
  await textarea.trigger('keydown', { key: 'Escape' });
  expect(w.find('textarea.segment-editor-input').exists()).toBe(false);

  // Open edit mode again
  await w.get('[data-action=edit-segment]').trigger('click');
  const textarea2 = w.get('textarea.segment-editor-input');
  await textarea2.setValue('Texto modificado final');

  // Click save
  await w.get('[data-action=save-segment]').trigger('click');
  await flushPromises();

  // Emitted transcript-updated or called update
  expect(w.emitted('update:transcript') || w.emitted('save') || w.emitted('update')).toBeTruthy();
});
