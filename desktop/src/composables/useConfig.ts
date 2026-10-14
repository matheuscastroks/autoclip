import { ref, computed } from 'vue';
import { api } from '../api';
import type { Config, GeminiConnection } from '../types';

export function useConfig() {
  const config = ref<Config | null>(null);

  const keyConfigured = computed(() => {
    if (!config.value) return false;
    return config.value.ai_provider === 'openrouter'
      ? Boolean(config.value.openrouter_key_configured)
      : Boolean(config.value.gemini_key_configured);
  });

  const setupMissing = computed(
    () =>
      !config.value ||
      !config.value.asr_available ||
      !config.value.tools_available ||
      !keyConfigured.value
  );

  async function loadConfig() {
    config.value = await api.config();
    return config.value;
  }

  async function saveConfig(value: Config) {
    config.value = await api.saveConfig(value);
    return config.value;
  }

  async function saveKey(key: string): Promise<GeminiConnection> {
    const result = await api.saveKey(key);
    config.value = await api.config();
    return result;
  }

  async function saveOpenRouterKey(key: string): Promise<{ configured: boolean }> {
    const result = await api.saveOpenRouterKey(key);
    config.value = await api.config();
    return result;
  }

  return {
    config,
    keyConfigured,
    setupMissing,
    loadConfig,
    saveConfig,
    saveKey,
    saveOpenRouterKey,
  };
}
