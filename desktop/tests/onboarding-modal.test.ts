import {mount} from '@vue/test-utils'
import {describe,it,expect,vi} from 'vitest'
import OnboardingModal from '../src/components/OnboardingModal.vue'

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
    tier_description: 'Recomendado para o seu setup com GPU dedicada'
  }

  it('renders hardware specs and recommended tier badge', () => {
    const wrapper = mount(OnboardingModal, {
      props: {
        profile: mockProfile,
        toolsMissing: true,
        asrMissing: true
      }
    })
    expect(wrapper.text()).toContain('RTX 3060')
    expect(wrapper.text()).toContain('Tier 3')
    expect(wrapper.find('[data-tier="3"]').classes()).toContain('recommended')
  })

  it('allows user to manually override recommended tier', async () => {
    const wrapper = mount(OnboardingModal, {
      props: {
        profile: mockProfile,
        toolsMissing: false,
        asrMissing: true
      }
    })
    const tier2Btn = wrapper.find('[data-tier="2"]')
    await tier2Btn.trigger('click')
    expect(wrapper.find('[data-tier="2"]').classes()).toContain('selected')
  })

  it('defaults ffmpeg checkbox based on toolsMissing prop', () => {
    const wrapper = mount(OnboardingModal, {
      props: {
        profile: mockProfile,
        toolsMissing: true,
        asrMissing: true
      }
    })
    const checkbox = wrapper.find<HTMLInputElement>('input[data-action="toggle-ffmpeg"]')
    expect(checkbox.element.checked).toBe(true)
  })
})
