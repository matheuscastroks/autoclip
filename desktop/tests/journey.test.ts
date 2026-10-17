import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import PipelinePanel from '../src/components/PipelinePanel.vue';
import type { Project, Revision } from '../src/types';

const project = {
  id: 'p',
  name: 'Entrevista',
  title: 'Entrevista',
  status: 'analyzed',
  has_transcript: true,
  has_analysis: true,
  word_count: 100,
  is_manual: false,
} as Project;
const preview = {
  revision_id: 'r',
  candidate_id: 'c',
  title: 'Trecho',
  technical_pass: false,
  review_status: 'needs_review',
  final_state: 'not_generated',
  warnings: [],
  preview: { state: 'available' },
} as Revision;

function panel(revisions: Revision[], selectedCandidateIds: string[] = ['c']) {
  return mount(PipelinePanel, {
    props: {
      project,
      jobs: [],
      busy: false,
      hasCuts: revisions.length > 0,
      revisions,
      selectedCount: selectedCandidateIds.length,
      selectedCandidateIds,
    },
  });
}

describe('contextual project journey', () => {
  it('distinguishes evaluating a preview from approving a final', async () => {
    const w = panel([preview]);
    expect(w.get('.state-hero-card').text()).toContain('Prévias prontas para avaliar');
    expect(w.get('.state-hero-card').text()).not.toContain('exporte');
    await w.get('.hero-primary-btn').trigger('click');
    expect(w.emitted('review')).toHaveLength(1);
    expect(w.find('.pipeline-aside').exists()).toBe(true);
    w.unmount();
  });

  it('offers new selected proposals even when older cuts already exist', () => {
    const w = panel([preview], ['c', 'new']);
    expect(w.get('.state-hero-card').text()).toContain('Gerar prévias rápidas');
    w.unmount();
  });

  it('makes export the next action only for technically valid approved finals', async () => {
    const w = panel([
      { ...preview, technical_pass: true, review_status: 'approved', final_state: 'available' },
    ]);
    expect(w.get('.hero-primary-btn').text()).toContain('Exportar aprovados');
    await w.get('.hero-primary-btn').trigger('click');
    expect(w.emitted('export')).toHaveLength(1);
    w.unmount();
  });

  it('asks for final review without generating or approving anything automatically', () => {
    const w = panel([{ ...preview, technical_pass: true, final_state: 'available' }]);
    expect(w.get('.state-hero-card').text()).toContain('Versões finais para revisar');
    expect(w.emitted('generate')).toBeUndefined();
    expect(w.emitted('export')).toBeUndefined();
    w.unmount();
  });

  it('keeps existing finals reviewable when the original analysis is unavailable', async () => {
    const w = panel([{ ...preview, technical_pass: true, final_state: 'available' }]);
    await w.setProps({ project: { ...project, has_analysis: false, has_transcript: false } });
    expect(w.get('.state-hero-card').text()).toContain('Versões finais para revisar');
    w.unmount();
  });
});
