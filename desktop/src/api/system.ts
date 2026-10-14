import { request, post } from './client';
import type { HardwareProfile, ProvisionStatus, ProvisionRequest } from '../types';

export const systemApi = {
  profile: () => request<{ schema_version: string; profile: HardwareProfile }>('/system/profile'),
  provision: (body: ProvisionRequest) => post<ProvisionStatus>('/system/provision', body),
  provisionStatus: () => request<ProvisionStatus>('/system/provision/status'),
  cancelProvision: () => post<{ cancelled: boolean }>('/system/provision/cancel'),
  pick: async (kind: string) => (await post<{ path: string | null }>('/picker', { kind })).path,
  shutdown: () => post<void>('/shutdown'),
};
