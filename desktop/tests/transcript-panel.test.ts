import { mount, flushPromises } from '@vue/test-utils';
import { it, expect, vi } from 'vitest';
import ProjectWorkspace from '../src/components/ProjectWorkspace.vue';
import TranscriptPanel from '../src/components/TranscriptPanel.vue';
import type { Project } from '../src/types';
const project = {
  id: 'p',
  name: 'Projeto',
  title: 'Entrevista',
  status: 'transcribed',
  word_count: 4,
  has_transcript: true,
  has_analysis: false,
  is_manual: false,
  warnings: [],
  revisions: [],
} as unknown as Project;
const transcript = {
  words: [],
  segments: [
    { id: 'a', text: 'Primeira afirmação.', start_us: 1_000_000, end_us: 4_000_000 },
    { id: 'b', text: 'Ressalva importante.', start_us: 5_000_000, end_us: 9_000_000 },
  ],
};
it('unloads original media when transcription becomes unavailable in the open panel', async () => {
  const w = mount(TranscriptPanel, {
    props: { transcript, sourceUrl: '/source.mp4', wordCount: 4 },
  });
  try {
    const video = w.get('video').element;
    await w.setProps({ transcript: null });
    expect(video.getAttribute('src')).toBeNull();
  } finally {
    w.unmount();
  }
});
it('seeks with a keyboard-accessible timestamp and follows playback without replacing selectable text', async () => {
  const play = vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue();
  const w = mount(ProjectWorkspace, {
    props: {
      project,
      transcript,
      revisions: [],
      jobs: [],
      sourceUrl: '/source.mp4',
      previewUrl: '',
      busy: false,
    },
  });
  try {
    await w.get('[role=tab]#tab-transcript').trigger('click');
    const timestamp = w.get('button[data-segment=b]');
    await timestamp.trigger('click');
    await flushPromises();
    const video = w.get('video').element as HTMLVideoElement;
    expect(video.currentTime).toBe(5);
    video.currentTime = 6;
    await w.get('video').trigger('timeupdate');
    expect(w.get('.transcript-segment-row.current').text()).toContain('Ressalva importante.');
    expect(w.get('.transcript-segment-row.current p').text()).toBe('Ressalva importante.');
    await w.get('[role=tab]#tab-analysis').trigger('click');
    expect(video.getAttribute('src')).toBeNull();
  } finally {
    w.unmount();
    play.mockRestore();
  }
});
it('preserves transcript search across project tabs and explains unavailable transcription', async () => {
  const w = mount(ProjectWorkspace, {
    props: {
      project,
      transcript,
      revisions: [],
      jobs: [],
      sourceUrl: '',
      previewUrl: '',
      busy: false,
    },
  });
  try {
    await w.get('#tab-transcript').trigger('click');
    await w.get('input[type=search]').setValue('ressalva');
    expect(w.findAll('.transcript-segment-row')).toHaveLength(1);
    await w.get('#tab-overview').trigger('click');
    await w.get('#tab-transcript').trigger('click');
    expect((w.get('input[type=search]').element as HTMLInputElement).value).toBe('ressalva');
    await w.setProps({ transcript: null });
    expect(w.text()).toContain('Ainda sem transcrição');
  } finally {
    w.unmount();
  }
});
