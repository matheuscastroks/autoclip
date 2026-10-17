import { mount } from '@vue/test-utils';
import { it, expect } from 'vitest';
import OutputGuidelinesCard from '../src/components/pipeline/OutputGuidelinesCard.vue';

it('allows choosing caption preset and playback speed', async () => {
  const w = mount(OutputGuidelinesCard, {
    props: {
      selectedPreset: 'karaoke-yellow-v1',
      selectedSpeed: '1.0x',
    },
  });

  expect(w.text()).toContain('Karaoke');
  expect(w.text()).toContain('1080×1920 (9:16)');

  const minimalPreset = w.get('[data-preset=clean-white-v1]');
  await minimalPreset.trigger('click');
  expect(w.emitted('update:preset')?.[0]).toEqual(['clean-white-v1']);

  const speedPill = w.get('[data-speed="1.1x"]');
  await speedPill.trigger('click');
  expect(w.emitted('update:speed')?.[0]).toEqual(['1.1x']);
});
