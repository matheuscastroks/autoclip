import { mount } from '@vue/test-utils';
import { it, expect } from 'vitest';
import PipelineMilestoneStepper from '../src/components/pipeline/PipelineMilestoneStepper.vue';

it('renders 4 human-friendly steps and flags current progress correctly', () => {
  const w = mount(PipelineMilestoneStepper, {
    props: {
      status: 'transcribed',
      hasTranscript: true,
      hasAnalysis: false,
      hasCuts: false,
    },
  });

  const steps = w.findAll('.milestone-step');
  expect(steps).toHaveLength(4);
  expect(steps[0].text()).toContain('Mídia Importada');
  expect(steps[0].classes()).toContain('is-completed');
  expect(steps[1].text()).toContain('Transcrição');
  expect(steps[1].classes()).toContain('is-completed');
  expect(steps[2].text()).toContain('Análise IA');
  expect(steps[2].classes()).toContain('is-current');
  expect(steps[3].text()).toContain('Cortes Prontos');
  expect(steps[3].classes()).toContain('is-pending');
});

it('marks transcription as active when status is transcribing', () => {
  const w = mount(PipelineMilestoneStepper, {
    props: {
      status: 'transcribing',
      hasTranscript: false,
      hasAnalysis: false,
      hasCuts: false,
      busy: true,
      activeOperation: 'transcribe',
    },
  });

  const steps = w.findAll('.milestone-step');
  expect(steps[1].classes()).toContain('is-running');
});

it('marks all steps as completed when cuts are ready', () => {
  const w = mount(PipelineMilestoneStepper, {
    props: {
      status: 'completed',
      hasTranscript: true,
      hasAnalysis: true,
      hasCuts: true,
    },
  });

  const steps = w.findAll('.milestone-step');
  expect(steps.every(s => s.classes().includes('is-completed'))).toBe(true);
});
