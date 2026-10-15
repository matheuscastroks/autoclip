import { ref } from 'vue';
import { it, expect } from 'vitest';
import { useProposalSelection } from '../src/composables/useProposalSelection';
import type { Proposal } from '../src/types';

it('rejects missing, ineligible and discarded candidates including saved selections', () => {
  const proposals = ref([
    { candidate_id: 'allowed', eligible: true, start_us: 0, end_us: 20 },
    { candidate_id: 'invalid', eligible: false, start_us: 30, end_us: 50 },
    { candidate_id: 'discarded', eligible: true, start_us: 60, end_us: 80 },
  ] as Proposal[]);
  const selection = useProposalSelection(proposals, ref(['discarded']));
  expect(selection.toggle('invalid')).toBe(false);
  expect(selection.toggle('discarded')).toBe(false);
  expect(selection.toggle('missing')).toBe(false);
  selection.setSelection(['allowed', 'invalid', 'discarded', 'missing']);
  expect(selection.validSelection.value).toEqual(['allowed']);
});
