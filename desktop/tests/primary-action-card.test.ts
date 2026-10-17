import { mount } from '@vue/test-utils';
import { it, expect } from 'vitest';
import PrimaryActionCard from '../src/components/pipeline/PrimaryActionCard.vue';

it('renders context-aware action button and reveals technical drawer on demand', async () => {
  const w = mount(PrimaryActionCard, {
    props: {
      status: 'transcribed',
      hero: {
        title: 'Transcrição Concluída',
        description: 'Pronto para analisar ganchos.',
        state: 'ready',
        primary: { id: 'analyze', label: 'Buscar Cortes com IA', disabled: false },
        secondary: [],
      },
      technicalSteps: [],
      busy: false,
    },
  });

  const btn = w.get('[data-action=primary-action]');
  expect(btn.text()).toBe('Buscar Cortes com IA');
  await btn.trigger('click');
  expect(w.emitted('action')).toBeTruthy();

  // Test technical details link exists and opens drawer (teleported to body)
  const link = w.get('[data-action=open-diagnostics]');
  await link.trigger('click');
  expect(document.querySelector('.diagnostics-drawer-overlay')).not.toBeNull();
});
