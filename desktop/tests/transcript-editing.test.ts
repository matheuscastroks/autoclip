import { mount, flushPromises } from '@vue/test-utils';
import { it, expect, vi } from 'vitest';
import TranscriptPanel from '../src/components/TranscriptPanel.vue';
import { api } from '../src/api';

it('enters edit mode on double-clicking segment text, saves on enter, cancels on esc', async () => {
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

  // Verify there are no edit or save buttons
  expect(w.find('[data-action=edit-segment]').exists()).toBe(false);
  expect(w.find('[data-action=save-segment]').exists()).toBe(false);
  expect(w.find('[data-action=cancel-segment]').exists()).toBe(false);

  // Double click the segment text to enter editing mode
  const textEl = w.get('.transcript-segment-row p');
  await textEl.trigger('dblclick');

  // Verify seamless textarea appears with current text
  const textarea = w.get('textarea.segment-editor-seamless');
  expect((textarea.element as HTMLTextAreaElement).value).toBe('Texto original');

  // Modify text
  await textarea.setValue('Texto modificado');

  // Cancel with Esc
  await textarea.trigger('keydown', { key: 'Escape' });
  expect(w.find('textarea.segment-editor-seamless').exists()).toBe(false);
  expect(w.get('.transcript-segment-row p').text()).toBe('Texto original');

  // Double click again to edit
  await w.get('.transcript-segment-row p').trigger('dblclick');
  const textarea2 = w.get('textarea.segment-editor-seamless');
  await textarea2.setValue('Texto modificado final');

  // Press Enter to save immediately
  await textarea2.trigger('keydown.enter');
  await flushPromises();

  // Emitted transcript-updated or called update
  expect(w.emitted('update:transcript') || w.emitted('save')).toBeTruthy();
  expect(api.updateTranscript).toHaveBeenCalledWith('p1', {
    segments: [{ id: 's1', text: 'Texto modificado final' }],
  });
});
