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
  it('keeps technical paths collapsed but reveals and focuses an invalid required field', async () => {
    const { wrapper } = setup();
    try {
      const details = wrapper.get('details.settings-paths');
      expect((details.element as HTMLDetailsElement).open).toBe(false);
      await wrapper.get('#settings-tab-2').trigger('click');
      const field = wrapper.get('.settings-paths input');
      await field.setValue('');
      await field.trigger('invalid');
      await flushPromises();
      expect(wrapper.get('#settings-tab-0').attributes('aria-selected')).toBe('true');
      expect((details.element as HTMLDetailsElement).open).toBe(true);
      expect(document.activeElement).toBe(field.element);
    } finally {
      wrapper.unmount();
    }
  });
  it('uses keyboard tabs without submitting or losing edited values', async () => {
    const { wrapper, saveConfig } = setup();
    await wrapper.get('.local-resources input').setValue('updated-model');
    await wrapper.get('[role=tablist]').trigger('keydown', { key: 'End' });
    expect(wrapper.get('#settings-tab-3').attributes('aria-selected')).toBe('true');
    expect(document.activeElement?.id).toBe('settings-tab-3');
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

  it('groups provider choices as one native radio control', () => {
    const { wrapper } = setup();
    const choices = wrapper.findAll('.provider-choice-group input[type="radio"]');
    expect(choices.length).toBeGreaterThanOrEqual(2);
    expect(choices.map(choice => choice.attributes('name'))).toEqual(
      choices.map(() => 'ai-provider')
    );
    const speeds = wrapper.findAll('.speed-choice-group input[type="radio"]');
    expect(speeds.length).toBe(3);
    expect(speeds.map(choice => choice.attributes('name'))).toEqual(
      speeds.map(() => 'playback-speed')
    );
    wrapper.unmount();
  });
});
