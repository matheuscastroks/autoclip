import { mount, flushPromises } from '@vue/test-utils';
import { describe, it, expect, vi } from 'vitest';
import SettingsPanel from '../src/components/SettingsPanel.vue';

function setup() {
  const saveConfig = vi.fn().mockResolvedValue(undefined);
  const wrapper = mount(SettingsPanel, {
    attachTo: document.body,
    props: {
      config: {
        asr_model_path: 'model',
        gemini_model: 'gemini-example',
        max_calls: 10,
        window_seconds: 600,
        max_text_chars: 60000,
        ffmpeg: 'ffmpeg',
        ffprobe: 'ffprobe',
        asr_available: false,
        tools_available: true,
        gemini_key_configured: false,
      },
      saveConfig,
      saveKey: vi.fn(),
      pick: vi.fn(),
    },
  });
  return { wrapper, saveConfig };
}

describe('settings navigation', () => {
  it('uses keyboard tabs without submitting or losing edited values', async () => {
    const { wrapper, saveConfig } = setup();
    await wrapper.get('.local-resources input').setValue('updated-model');
    await wrapper.get('[role=tablist]').trigger('keydown', { key: 'End' });
    expect(wrapper.get('#settings-tab-2').attributes('aria-selected')).toBe('true');
    expect(document.activeElement?.id).toBe('settings-tab-2');
    await wrapper.get('[role=tablist]').trigger('keydown', { key: 'Home' });
    expect((wrapper.get('.local-resources input').element as HTMLInputElement).value).toBe(
      'updated-model'
    );
    expect(saveConfig).not.toHaveBeenCalled();
    expect(wrapper.text()).not.toContain('Próximo passo');
    wrapper.unmount();
  });

  it('submits exactly once through the native save button', async () => {
    const { wrapper, saveConfig } = setup();
    await wrapper.get('[data-action=save-config]').trigger('click');
    await flushPromises();
    expect(saveConfig).toHaveBeenCalledTimes(1);
    expect(wrapper.text()).toContain('Modelo local não encontrado');
    wrapper.unmount();
  });
});
