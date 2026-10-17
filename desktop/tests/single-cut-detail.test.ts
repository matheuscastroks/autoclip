import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import SingleCutDetailView from '../src/components/SingleCutDetailView.vue';
import type { EnrichedCut } from '../src/components/AllCutsView.vue';

vi.mock('../src/api', () => ({
  api: {
    media: vi.fn(async () => 'blob:http://localhost/video.mp4'),
  },
}));

function makeCut(overrides: Partial<EnrichedCut['revision']> = {}): EnrichedCut {
  return {
    project: {
      id: 'proj-1',
      name: 'Projeto Teste',
      title: 'Projeto Teste',
      path: '/path/proj-1',
      duration_us: 60_000_000,
      status: 'completed',
      has_transcript: true,
      has_analysis: true,
      word_count: 500,
      revisions: [],
      is_manual: false,
      warnings: [],
      created_at: '',
      updated_at: 0,
      source: null,
      error: null,
    },
    revision: {
      revision_id: 'rev-1',
      title: 'Corte Incrível',
      technical_pass: false,
      review_status: 'needs_review',
      warnings: [],
      exported: false,
      final_state: 'not_generated',
      duration_us: 30_000_000,
      ...overrides,
    },
  };
}

describe('SingleCutDetailView', () => {
  it('requires final render before enabling human editorial checklist', () => {
    const cut = makeCut({ final_state: 'not_generated', technical_pass: false });
    const wrapper = mount(SingleCutDetailView, { props: { cut } });

    // Step 2 should offer final render
    expect(wrapper.text()).toContain('Gerar Versão Final 1080×1920');
    // Step 3 (Approval) should be locked waiting for final
    expect(wrapper.text()).toContain('Aguardando geração da versão final para inspeção editorial');
    expect(wrapper.findAll('.criterion-checkbox')).toHaveLength(0);
    wrapper.unmount();
  });

  it('displays 5 criteria checkboxes when final is available and disables approval until all are checked', async () => {
    const cut = makeCut({
      final_state: 'available',
      technical_pass: true,
      content_hash: 'hash123',
    });
    const wrapper = mount(SingleCutDetailView, { props: { cut } });

    const checkboxes = wrapper.findAll<HTMLInputElement>('.criterion-checkbox');
    expect(checkboxes).toHaveLength(5);

    // Approve button should be disabled initially
    const approveBtn = wrapper.findAll('button').find(b => b.text().includes('Aprovar Corte'))!;
    expect(approveBtn.attributes('disabled')).toBeDefined();

    // Check 4 of the 5 criteria
    for (let i = 0; i < 4; i++) {
      await checkboxes[i].setValue(true);
    }
    expect(approveBtn.attributes('disabled')).toBeDefined();

    // Check the 5th criterion
    await checkboxes[4].setValue(true);
    expect(approveBtn.attributes('disabled')).toBeUndefined();

    // Click approve and verify emitted payload includes the cut and confirmed checks
    await approveBtn.trigger('click');
    expect(wrapper.emitted('approve')).toBeTruthy();
    const emittedData = wrapper.emitted('approve')![0] as [EnrichedCut, Record<string, boolean>];
    expect(emittedData[0].revision.revision_id).toBe('rev-1');
    expect(emittedData[1]).toEqual({
      completeness: true,
      context: true,
      qualifications: true,
      words_and_boundaries: true,
      audiovisual: true,
    });

    wrapper.unmount();
  });

  it('shows export action when cut is approved', () => {
    const cut = makeCut({
      final_state: 'available',
      technical_pass: true,
      review_status: 'approved',
      exported: false,
    });
    const wrapper = mount(SingleCutDetailView, { props: { cut } });

    expect(wrapper.text()).toContain('Exportar Corte');
    expect(wrapper.text()).toContain('Vídeo pronto para exportação');
    wrapper.unmount();
  });
});
