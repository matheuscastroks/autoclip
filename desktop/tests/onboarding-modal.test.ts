import { mount, flushPromises } from '@vue/test-utils';
import { describe, it, expect, vi } from 'vitest';
import OnboardingModal from '../src/components/OnboardingModal.vue';
import { api } from '../src/api';
import type { ProvisionStatus } from '../src/types';

describe('OnboardingModal', () => {
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
