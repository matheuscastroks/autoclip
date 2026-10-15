import type { Revision } from '../types';

// Legacy revisions predate final_state; explicit invalid/not_generated is never final.
export function isFinalAvailable(revision: Revision): boolean {
  return revision.technical_pass && (!revision.final_state || revision.final_state === 'available');
}

export function isExportable(revision: Revision): boolean {
  return isFinalAvailable(revision) && revision.review_status === 'approved';
}
