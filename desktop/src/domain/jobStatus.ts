export type JobStatus =
  | 'ready'
  | 'pending'
  | 'running'
  | 'processing'
  | 'cancelling'
  | 'cancelled'
  | 'failed'
  | 'interrupted'
  | 'completed'
  | 'approved'
  | 'rejected'
  | 'needs_review'
  | 'invalid';

export const FAILED_STATUSES: readonly JobStatus[] = [
  'failed',
  'cancelled',
  'interrupted',
] as const;

export const RUNNING_STATUSES: readonly JobStatus[] = [
  'running',
  'cancelling',
  'processing',
] as const;

export const ACTIVE_STATUSES: readonly JobStatus[] = [
  'pending',
  'running',
  'processing',
  'cancelling',
] as const;

export function isFailed(status: string): boolean {
  return (FAILED_STATUSES as readonly string[]).includes(status as JobStatus);
}

export function isRunning(status: string): boolean {
  return (RUNNING_STATUSES as readonly string[]).includes(status as JobStatus);
}

export function isActive(status: string): boolean {
  return (ACTIVE_STATUSES as readonly string[]).includes(status as JobStatus);
}

export type StatusTagType = 'success' | 'warning' | 'danger' | 'info' | 'primary';

export function statusTagType(status: string): StatusTagType {
  switch (status) {
    case 'ready':
    case 'completed':
    case 'approved':
      return 'success';
    case 'running':
    case 'processing':
    case 'cancelling':
      return 'primary';
    case 'failed':
    case 'interrupted':
      return 'danger';
    case 'needs_review':
    case 'cancelled':
    case 'rejected':
      return 'warning';
    case 'pending':
    case 'pending_import':
    default:
      return 'info';
  }
}
