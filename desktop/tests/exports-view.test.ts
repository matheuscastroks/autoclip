import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import ExportsView, { type ExportedCutItem } from '../src/components/ExportsView.vue';

function makeExported(overrides: Partial<ExportedCutItem['revision']> = {}): ExportedCutItem {
  return {
    project: {
      id: 'proj-1',
      name: 'Podcast Especial',
      title: 'Podcast Especial',
      path: '/path/proj-1',
      duration_us: 120_000_000,
      status: 'completed',
      has_transcript: true,
      has_analysis: true,
      word_count: 800,
      revisions: [],
      is_manual: false,
      warnings: [],
      created_at: '',
      updated_at: 0,
      source: null,
      error: null,
    },
    revision: {
      revision_id: 'rev-export-1',
      title: 'O Segredo da Narrativa',
      technical_pass: true,
      review_status: 'approved',
      warnings: [],
      exported: true,
      final_state: 'available',
      duration_us: 45_000_000,
      ...overrides,
    },
  };
}

describe('ExportsView', () => {
  it('uses the AI-generated editorial description instead of generic text when available', () => {
    const aiCopy = 'Descubra como estruturar uma narrativa cativante do zero. #storytelling #cinema';
    const item = makeExported({ description: aiCopy });
    const wrapper = mount(ExportsView, {
      props: { exportedCuts: [item] },
    });

    expect(wrapper.find('.copy-content-preview').text()).toBe(aiCopy);
    wrapper.unmount();
  });

  it('falls back to the cut title when description is absent', () => {
    const item = makeExported({ description: null, title: 'Título sem descrição' });
    const wrapper = mount(ExportsView, {
      props: { exportedCuts: [item] },
    });

    expect(wrapper.find('.copy-content-preview').text()).toContain('Título sem descrição');
    expect(wrapper.find('.copy-content-preview').text()).toContain('#shorts');
    wrapper.unmount();
  });
});
