import { mount, flushPromises } from '@vue/test-utils';
import { describe, it, expect, vi } from 'vitest';
import OnboardingModal from '../src/components/OnboardingModal.vue';
import { api } from '../src/api';
import type { ProvisionStatus } from '../src/types';

describe('OnboardingModal', () => {
  it('saves the chosen provider once and clears credential text only after success', async () => {
    const ready = {
      status: 'ready',
      stage: 'complete',
      item: 'fixture',
      downloaded_bytes: 1,
      total_bytes: 1,
      speed_bps: 0,
      percent: 100,
      error: null,
    } as ProvisionStatus;
    const provision = vi.spyOn(api, 'provision').mockResolvedValue(ready);
    const poll = vi.spyOn(api, 'provisionStatus').mockResolvedValue(ready);
    const gemini = vi.fn();
    const router = vi.fn().mockResolvedValue({ configured: true });
    const wrapper = mount(OnboardingModal, {
      props: {
        profile: null,
        toolsMissing: true,
        asrMissing: true,
        saveKey: gemini,
        saveOpenRouterKey: router,
      },
    });
    try {
      await wrapper.get('[data-action=start-provision]').trigger('click');
      await vi.waitFor(() => expect(wrapper.find('.key-text-input').exists()).toBe(true), {
        timeout: 3000,
      });
      await wrapper.findAll('.provider-pills button')[1].trigger('click');
      await wrapper.get('.key-text-input').setValue('fixture-router-key');
      await wrapper.get('.api-key-card .button.primary').trigger('click');
      await flushPromises();
      expect(router).toHaveBeenCalledExactlyOnceWith('fixture-router-key');
      expect(gemini).not.toHaveBeenCalled();
      expect((wrapper.get('.key-text-input').element as HTMLInputElement).value).toBe('');
      expect(wrapper.get('.success-pill-msg').text()).toContain('Chave salva');
      expect(wrapper.get('.success-pill-msg').text()).not.toContain('validada');
    } finally {
      wrapper.unmount();
      provision.mockRestore();
      poll.mockRestore();
    }
  });
  it('waits for credential persistence and reports failure without a false saved state', async () => {
    const ready = {
      status: 'ready',
      stage: 'complete',
      item: 'fixture',
      downloaded_bytes: 1,
      total_bytes: 1,
      speed_bps: 0,
      percent: 100,
      error: null,
    } as ProvisionStatus;
    const provision = vi.spyOn(api, 'provision').mockResolvedValue(ready);
    const poll = vi.spyOn(api, 'provisionStatus').mockResolvedValue(ready);
    let fail!: (error: Error) => void;
    const save = vi.fn().mockImplementation(
      () =>
        new Promise((_resolve, reject) => {
          fail = reject;
        })
    );
    const wrapper = mount(OnboardingModal, {
      props: { profile: null, toolsMissing: true, asrMissing: true, saveKey: save },
    });
    try {
      await wrapper.get('[data-action=start-provision]').trigger('click');
      await vi.waitFor(() => expect(wrapper.find('.key-text-input').exists()).toBe(true), {
        timeout: 3000,
      });
      await wrapper.get('.key-text-input').setValue('fixture-key');
      await wrapper.get('.api-key-card .button.primary').trigger('click');
      expect(wrapper.find('.success-pill-msg').exists()).toBe(false);
      expect(save).toHaveBeenCalledWith('fixture-key');
      await wrapper.get('.api-key-card .button.primary').trigger('click');
      expect(save).toHaveBeenCalledTimes(1);
      expect(
        wrapper
          .findAll('.provider-pills button')
          .every(button => button.attributes('disabled') !== undefined)
      ).toBe(true);
      expect(
        (wrapper.get('.api-key-card .button.primary').element as HTMLButtonElement).disabled
      ).toBe(true);
      fail(new Error('Não foi possível armazenar a chave.'));
      await flushPromises();
      expect(wrapper.get('[role=alert]').text()).toContain('Não foi possível armazenar');
      expect(wrapper.find('.success-pill-msg').exists()).toBe(false);
      expect((wrapper.get('.key-text-input').element as HTMLInputElement).value).toBe(
        'fixture-key'
      );
    } finally {
      wrapper.unmount();
      provision.mockRestore();
      poll.mockRestore();
    }
  });
  const mockProfile = {
    cpu_physical_cores: 8,
    cpu_logical_cores: 16,
    ram_total_gb: 16.0,
    ram_available_gb: 11.2,
    has_cuda: true,
    gpu_name: 'NVIDIA GeForce RTX 3060',
    vram_gb: 6.0,
    recommended_tier: 3,
    recommended_model_id: 'Systran/faster-whisper-large-v3-turbo',
    tier_title: 'Tier 3 (Alta Performance)',
    tier_description: 'Recomendado para o seu setup com GPU dedicada',
  };

  it('renders hardware specs and recommended tier badge', () => {
    const wrapper = mount(OnboardingModal, {
      props: {
        profile: mockProfile,
        toolsMissing: true,
        asrMissing: true,
      },
    });
    expect(wrapper.text()).toContain('RTX 3060');
    expect(wrapper.text()).toContain('Tier 3');
    expect(wrapper.find('[data-tier="3"]').classes()).toContain('recommended');
  });

  it('allows user to manually override recommended tier', async () => {
    const wrapper = mount(OnboardingModal, {
      props: {
        profile: mockProfile,
        toolsMissing: false,
        asrMissing: true,
      },
    });
    const tier2Btn = wrapper.find('[data-tier="2"]');
    expect(tier2Btn.attributes('aria-pressed')).toBe('false');
    await tier2Btn.trigger('click');
    expect(wrapper.find('[data-tier="2"]').classes()).toContain('selected');
    expect(tier2Btn.attributes('aria-pressed')).toBe('true');
  });

  it('defaults ffmpeg checkbox based on toolsMissing prop', () => {
    const wrapper = mount(OnboardingModal, {
      props: {
        profile: mockProfile,
        toolsMissing: true,
        asrMissing: true,
      },
    });
    const checkbox = wrapper.find<HTMLInputElement>('input[data-action="toggle-ffmpeg"]');
    expect(checkbox.element.checked).toBe(true);
  });

  it('lets the user defer missing tools to consult existing projects', async () => {
    const wrapper = mount(OnboardingModal, {
      props: { profile: mockProfile, toolsMissing: true, asrMissing: true },
    });
    await wrapper.get('[data-action=defer-setup]').trigger('click');
    expect(wrapper.emitted('close')).toHaveLength(1);
    wrapper.unmount();
  });

  it('shows a cancellation failure while keeping installation status available', async () => {
    const status: ProvisionStatus = {
      status: 'downloading',
      stage: 'download',
      item: 'fixture',
      downloaded_bytes: 0,
      total_bytes: 100,
      speed_bps: 0,
      percent: 0,
      error: null,
    };
    const provision = vi.spyOn(api, 'provision').mockResolvedValue(status);
    const poll = vi.spyOn(api, 'provisionStatus').mockResolvedValue(status);
    const cancel = vi
      .spyOn(api, 'cancelProvision')
      .mockRejectedValue(new Error('Falha ao cancelar instalação'));
    const wrapper = mount(OnboardingModal, {
      props: { profile: mockProfile, toolsMissing: true, asrMissing: true },
    });
    try {
      await wrapper.get('[data-action=start-provision]').trigger('click');
      await flushPromises();
      await wrapper.get('[data-action=cancel-provision]').trigger('click');
      await flushPromises();
      expect(wrapper.get('.onboarding-error-banner').text()).toContain(
        'Falha ao cancelar instalação'
      );
      expect(wrapper.find('[data-action=cancel-provision]').exists()).toBe(true);
    } finally {
      wrapper.unmount();
      provision.mockRestore();
      poll.mockRestore();
      cancel.mockRestore();
    }
  });
});
