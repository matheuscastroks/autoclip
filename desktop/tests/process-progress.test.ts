import { mount } from '@vue/test-utils';
import { afterEach, expect, it, vi } from 'vitest';
import ProcessProgress from '../src/components/ui/ProcessProgress.vue';

afterEach(() => vi.useRealTimers());

it('distinguishes measured stage from estimated overall progress', () => {
  const wrapper = mount(ProcessProgress, {
    props: {
      progress: {
        stage: 'transcribe',
        steps: {},
        phase: 'transcribe',
        stage_percent: 25,
        overall_percent: 20,
        stage_eta_seconds: 40,
        eta_seconds: 60,
      },
      status: 'running',
    },
  });
  expect(wrapper.get('[role=progressbar]').attributes('value')).toBe('25');
  expect(wrapper.text()).toContain('25% da etapa');
  expect(wrapper.text()).toContain('20% total estimado');
  expect(wrapper.text()).toContain('~1 min restante');
  wrapper.unmount();
});

it('does not manufacture percentages while the worker fails to initialize', async () => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date('2026-10-15T12:00:00Z'));
  const wrapper = mount(ProcessProgress, {
    props: { startedAt: '2026-10-15T12:00:00Z', status: 'running' },
  });
  await vi.advanceTimersByTimeAsync(31_000);
  expect(wrapper.get('[role=progressbar]').attributes('value')).toBeUndefined();
  expect(wrapper.text()).toContain('Inicialização demorando');
  expect(wrapper.text()).not.toContain('100%');
  wrapper.unmount();
});

it('heartbeat is not evidence of advancement and warnings stop on completion', async () => {
  const wrapper = mount(ProcessProgress, {
    props: {
      status: 'running',
      progress: { stage: 'analyze', steps: {}, stage_percent: 50, warning: 'no_advance' },
    },
  });
  expect(wrapper.text()).toContain('Sem avanço registrado');
  await wrapper.setProps({ status: 'failed' });
  expect(wrapper.text()).not.toContain('Sem avanço registrado');
  expect(wrapper.get('[role=progressbar]').attributes('value')).toBe('50');
  wrapper.unmount();
});

it('unknown download totals show transferred bytes rather than zero percent', () => {
  const wrapper = mount(ProcessProgress, {
    props: {
      progress: {
        stage: 'download',
        steps: {},
        stage_percent: null,
        completed_units: 1048576,
        unit: 'bytes',
      },
    },
  });
  expect(wrapper.text()).toContain('1.0 MB');
  expect(wrapper.get('[role=progressbar]').attributes('value')).toBeUndefined();
  expect(wrapper.text()).not.toContain('0%');
  wrapper.unmount();
});
