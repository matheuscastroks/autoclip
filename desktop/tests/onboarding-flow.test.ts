import { mount, flushPromises } from '@vue/test-utils';
import { it, expect, vi } from 'vitest';
import App from '../src/App.vue';
import OnboardingModal from '../src/components/OnboardingModal.vue';
let dependenciesReady = false;
vi.mock('../src/api', () => ({
  api: {
    projects: async () => [],
    jobs: async () => [],
    systemProfile: async () => ({ profile: null }),
    config: async () => ({
      asr_model_path: 'fixture',
      gemini_model: 'fixture',
      max_calls: 10,
      window_seconds: 600,
      max_text_chars: 60000,
      ffmpeg: 'ffmpeg',
      ffprobe: 'ffprobe',
      asr_available: dependenciesReady,
      tools_available: dependenciesReady,
      gemini_key_configured: false,
    }),
  },
}));

it('keeps onboarding open for credentials after dependencies become ready until explicit close', async () => {
  dependenciesReady = false;
  const w = mount(App, { attachTo: document.body });
  try {
    await flushPromises();
    expect(w.findComponent(OnboardingModal).exists()).toBe(true);
    dependenciesReady = true;
    w.getComponent(OnboardingModal).vm.$emit('configured');
    await flushPromises();
    expect(w.findComponent(OnboardingModal).exists()).toBe(true);
    w.getComponent(OnboardingModal).vm.$emit('close');
    await flushPromises();
    expect(w.findComponent(OnboardingModal).exists()).toBe(false);
    expect(w.text()).toContain('Adicionar chave Gemini');
  } finally {
    w.unmount();
  }
});
