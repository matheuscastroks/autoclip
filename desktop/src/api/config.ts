import { request, post, put } from './client';
import type { Config, GeminiConnection } from '../types';

export const configApi = {
  get: () => request<Config>('/config'),
  save: (config: Config) =>
    put<Config>('/config', {
      ...Object.fromEntries(
        Object.entries(config).filter(
          ([k]) =>
            ![
              'schema_version',
              'asr_available',
              'tools_available',
              'gemini_key_configured',
              'openrouter_key_configured',
            ].includes(k)
        )
      ),
    }),
  saveGeminiKey: (key: string) => put<GeminiConnection>('/config/credential', { key }),
  saveOpenRouterKey: (key: string) =>
    put<{ configured: boolean }>('/config/openrouter-credential', { key }),
  geminiConnection: () => request<GeminiConnection>('/config/gemini'),
  testGemini: () => post<GeminiConnection>('/config/gemini/test'),
};
