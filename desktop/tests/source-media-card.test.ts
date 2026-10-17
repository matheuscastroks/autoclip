import { mount } from '@vue/test-utils';
import { it, expect } from 'vitest';
import SourceMediaCard from '../src/components/pipeline/SourceMediaCard.vue';

it('renders video element and human-readable metadata badges', () => {
  const w = mount(SourceMediaCard, {
    props: {
      sourceUrl: '/videos/sample.mp4',
      durationUs: 125_000_000, // 2m 5s
      wordCount: 350,
      title: 'Entrevista Podcast',
    },
  });

  expect(w.find('video').exists()).toBe(true);
  expect(w.text()).toContain('2:05');
  expect(w.text()).toContain('350 palavras');
  expect(w.text()).toContain('Entrevista Podcast');
});

it('renders friendly placeholder when source media is missing', () => {
  const w = mount(SourceMediaCard, {
    props: {
      sourceUrl: '',
      title: 'Sem Vídeo',
    },
  });

  expect(w.find('video').exists()).toBe(false);
  expect(w.text()).toContain('Vídeo original não disponível');
});
