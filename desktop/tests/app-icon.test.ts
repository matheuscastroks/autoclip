import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import AppIcon from '../src/components/ui/AppIcon.vue';
import AppRail from '../src/components/layout/AppRail.vue';

describe('compiled Fluent icons', () => {
  it.each([
    'key',
    'eye',
    'eye-off',
    'save',
    'cpu',
    'sparkle',
    'check-circle',
    'stop',
    'open-external',
    'spinner',
    'download',
    'globe',
  ])('bundles the %s support icon as safe offline SVG', name => {
    const w = mount(AppIcon, { props: { name: name as 'projects' } });
    try {
      expect(w.find('svg').exists()).toBe(true);
      expect(w.find('path').exists()).toBe(true);
      expect(w.find('img,image,use,script,foreignObject').exists()).toBe(false);
    } finally {
      w.unmount();
    }
  });
  it('includes the live queue count in the accessible command name', () => {
    const w = mount(AppRail, {
      props: { activePage: 'projects', activeJobsCount: 3, engineState: 'online' },
    });
    try {
      expect(w.get('button[title="Fila global de tarefas"]').attributes('aria-label')).toContain(
        '3 tarefas ativas'
      );
    } finally {
      w.unmount();
    }
  });
  it('renders an inline decorative SVG without external resources', () => {
    const w = mount(AppIcon, { props: { name: 'projects' } });
    expect(w.element.tagName.toLowerCase()).toBe('svg');
    expect(w.attributes('aria-hidden')).toBe('true');
    expect(w.attributes('focusable')).toBe('false');
    expect(w.findAll('path').length).toBeGreaterThan(0);
    expect(w.find('img, image, use, script, foreignObject').exists()).toBe(false);
    expect(w.attributes('class')).toContain('app-icon--md');
  });
  it('exposes informative labels without adding a focus stop', () => {
    const w = mount(AppIcon, {
      props: { name: 'queue', decorative: false, label: 'Tarefas em andamento', size: 'lg' },
    });
    expect(w.attributes('role')).toBe('img');
    expect(w.attributes('aria-label')).toBe('Tarefas em andamento');
    expect(w.attributes('aria-hidden')).toBeUndefined();
    expect(w.attributes('tabindex')).toBeUndefined();
    expect(w.attributes('class')).toContain('app-icon--lg');
  });
  it('switches regular/filled geometry and supplies a semantic label when needed', async () => {
    const w = mount(AppIcon, { props: { name: 'projects', decorative: false, size: 'sm' } });
    const path = w.get('path').attributes('d');
    expect(w.attributes('aria-label')).toBe('Projetos');
    await w.setProps({ variant: 'filled' });
    expect(w.get('path').attributes('d')).not.toBe(path);
    expect(w.attributes('class')).toContain('app-icon--sm');
  });
  it('does not turn unexpected runtime names into arbitrary components or requests', () => {
    const w = mount(AppIcon, { props: { name: '__proto__' as 'projects' } });
    expect(w.find('svg').exists()).toBe(false);
    expect(w.find('img, image, script').exists()).toBe(false);
  });
});
