import { mount } from '@vue/test-utils';
import { expect, it } from 'vitest';
import ProjectTabs from '../src/components/layout/ProjectTabs.vue';

it('moves focus and selection with arrows, Home and End without submitting', async () => {
  const w = mount(ProjectTabs, {
    attachTo: document.body,
    props: { modelValue: 'overview', counts: { transcript: 120, analysis: 3, cuts: 2 } },
  });
  try {
    await w.get('[role=tablist]').trigger('keydown', { key: 'End' });
    expect(w.emitted('update:modelValue')?.at(-1)).toEqual(['cuts']);
    expect(document.activeElement?.id).toBe('tab-cuts');
    await w.setProps({ modelValue: 'cuts' });
    await w.get('[role=tablist]').trigger('keydown', { key: 'ArrowRight' });
    expect(w.emitted('update:modelValue')?.at(-1)).toEqual(['overview']);
    await w.get('[role=tablist]').trigger('keydown', { key: 'Home' });
    expect(document.activeElement?.id).toBe('tab-overview');
    expect(w.get('#tab-analysis').text()).toContain('3');
    expect(w.get('#tab-cuts').attributes('aria-controls')).toBe('project-panel');
    expect(w.findAll('[role=tab][tabindex="0"]')).toHaveLength(1);
  } finally {
    w.unmount();
  }
});
