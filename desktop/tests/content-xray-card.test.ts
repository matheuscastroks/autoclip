import { mount } from '@vue/test-utils';
import { it, expect } from 'vitest';
import ContentXRayCard from '../src/components/pipeline/ContentXRayCard.vue';

it('displays friendly placeholder before analysis and shows topic chips when ready', async () => {
  const w = mount(ContentXRayCard, {
    props: {
      hasTranscript: true,
      analysis: {
        state: 'completed',
        proposals: [
          { candidate_id: 'c1', topic_title: 'Produtividade Pessoal' },
          { candidate_id: 'c2', topic_title: 'Dicas de Foco' },
        ],
        topics: [
          { id: 't1', title: 'Produtividade Pessoal' },
          { id: 't2', title: 'Dicas de Foco' },
        ],
      } as any,
    },
  });

  expect(w.text()).toContain('Produtividade Pessoal');
  expect(w.text()).toContain('Dicas de Foco');
  expect(w.text()).toContain('2 propostas de cortes');

  const btn = w.get('[data-action=open-transcript]');
  await btn.trigger('click');
  expect(w.emitted('openTranscript')).toBeTruthy();
});

it('renders placeholder when transcript is not ready yet', () => {
  const w = mount(ContentXRayCard, {
    props: {
      hasTranscript: false,
    },
  });

  expect(w.text()).toContain('Raio-X Pendente');
  expect(w.text()).toContain('Após a transcrição');
});
