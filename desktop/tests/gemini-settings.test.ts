import { mount, flushPromises } from '@vue/test-utils';
import { describe, it, expect, vi } from 'vitest';
import SettingsPanel from '../src/components/SettingsPanel.vue';
import AppSelect from '../src/components/AppSelect.vue';
import { notify } from '../src/notifications';
const config = {
  asr_model_path: '/model',
  gemini_model: 'gemini-2.5-flash',
  max_calls: 10,
  window_seconds: 600,
  max_text_chars: 60000,
  ffmpeg: '/ffmpeg',
  ffprobe: '/probe',
  asr_available: true,
  tools_available: true,
  gemini_key_configured: true,
};
const valid = {
  status: 'valid' as const,
  configured: true,
  checked_at: '2026-10-12T12:00:00Z',
  message: 'Conexão validada.',
  models: [
    { id: 'gemini-3.8-flash', name: 'models/gemini-3.8-flash', display_name: 'Gemini 3.8 Flash' },
    { id: 'gemini-2.5-flash', name: 'models/gemini-2.5-flash', display_name: 'Gemini 2.5 Flash' },
  ],
};
function props() {
  return {
    config,
    saveConfig: vi.fn().mockResolvedValue(undefined),
    saveKey: vi.fn().mockResolvedValue(valid),
    pick: vi.fn(),
    getConnection: vi.fn().mockResolvedValue({ ...valid, status: 'untested', models: [] }),
    testConnection: vi.fn().mockResolvedValue(valid),
  };
}
describe('dynamic Gemini settings', () => {
  it('loads actual IDs from the catalog and saves exact selection', async () => {
    const p = props();
    const w = mount(SettingsPanel, { props: p });
    await flushPromises();
    await w.get('[data-action=test-gemini]').trigger('click');
    await flushPromises();
    const select = w.get('[data-field=gemini-model]');
    expect(select.attributes('role')).toBe('combobox');
    expect(w.findAllComponents(AppSelect)[0].props('options')).toEqual(
      expect.arrayContaining([expect.objectContaining({ value: 'gemini-3.8-flash' })])
    );
    w.findAllComponents(AppSelect)[0].vm.$emit('update:modelValue', 'gemini-3.8-flash');
    await flushPromises();
    await w.get('.settings-main').trigger('submit');
    await flushPromises();
    expect(p.saveConfig).toHaveBeenCalledWith(
      expect.objectContaining({ gemini_model: 'gemini-3.8-flash' })
    );
    w.unmount();
  });
  it('shows validating state then valid and clears the key', async () => {
    const p = props();
    let resolve: (v: typeof valid) => void = () => {};
    p.saveKey.mockImplementation(() => new Promise(r => (resolve = r)));
    const w = mount(SettingsPanel, { props: p });
    await flushPromises();
    await w.get('input[type=password]').setValue('fixture-secret');
    await w.get('[data-action=save-key]').trigger('click');
    expect(w.text()).toContain('Validando');
    resolve(valid);
    await flushPromises();
    expect(w.text()).toContain('Conexão validada');
    expect((w.get('input[type=password]').element as HTMLInputElement).value).toBe('');
    w.unmount();
  });
  it('keeps current model when it disappears and requires another explicit choice', async () => {
    const p = props();
    p.testConnection.mockResolvedValue({ ...valid, models: [valid.models[0]] });
    const w = mount(SettingsPanel, { props: p });
    await flushPromises();
    await w.get('[data-action=test-gemini]').trigger('click');
    await flushPromises();
    expect(w.text()).toContain('não aparece no catálogo');
    expect(w.findAllComponents(AppSelect)[0].props('modelValue')).toBe('gemini-2.5-flash');
    expect((w.get('[data-action=save-config]').element as HTMLButtonElement).disabled).toBe(true);
    w.unmount();
  });
  it('failed replacement does not claim success or discard the active catalog', async () => {
    const errorToast = vi.spyOn(notify, 'error');
    const p = props();
    p.getConnection.mockResolvedValue(valid);
    p.saveKey.mockRejectedValue(new Error('Chave inválida. A chave anterior permanece salva.'));
    const w = mount(SettingsPanel, { props: p });
    await flushPromises();
    await w.get('input[type=password]').setValue('invalid-fixture');
    await w.get('[data-action=save-key]').trigger('click');
    await flushPromises();
    expect(errorToast).toHaveBeenCalledWith('Chave inválida. A chave anterior permanece salva.');
    expect(w.find('.notice').exists()).toBe(false);
    expect(w.findAllComponents(AppSelect)[0].props('options')).toEqual(
      expect.arrayContaining([expect.objectContaining({ value: 'gemini-3.8-flash' })])
    );
    w.unmount();
  });
});
