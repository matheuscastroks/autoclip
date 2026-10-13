import {mount,flushPromises} from '@vue/test-utils'
import {describe,it,expect,vi} from 'vitest'
import SettingsPanel from '../src/components/SettingsPanel.vue'

const config={
  asr_model_path:'/model',
  gemini_model:'gemini-2.5-flash',
  max_calls:10,
  window_seconds:600,
  max_text_chars:60000,
  ffmpeg:'/ffmpeg',
  ffprobe:'/probe',
  asr_available:true,
  tools_available:true,
  gemini_key_configured:false,
  ai_provider:'gemini' as const,
  openrouter_model:'openrouter/free',
  openrouter_key_configured:false
}

function props(overrides={}){
  return {
    config:{...config,...overrides},
    saveConfig:vi.fn().mockResolvedValue(undefined),
    saveKey:vi.fn().mockResolvedValue(undefined),
    saveOpenRouterKey:vi.fn().mockResolvedValue({configured:true}),
    pick:vi.fn(),
    getConnection:vi.fn().mockResolvedValue({status:'untested',configured:false,checked_at:null,message:'',models:[]}),
    testConnection:vi.fn().mockResolvedValue({status:'valid',configured:true,checked_at:null,message:'',models:[]})
  }
}

describe('OpenRouter settings in SettingsPanel',()=>{
  it('switches provider to OpenRouter and reveals OpenRouter key panel and model choices',async()=>{
    const p=props()
    const w=mount(SettingsPanel,{props:p})
    await flushPromises()
    // Navigate to step 1 (IA & Modelos)
    await w.get('#settings-tab-1').trigger('click')
    await flushPromises()

    // Initially Gemini is selected
    expect(w.find('[data-field="provider-gemini"]').exists()).toBe(true)
    expect(w.find('[data-action="test-gemini"]').exists()).toBe(true)

    // Switch to OpenRouter
    await w.get('[data-field="provider-openrouter"]').trigger('click')
    await flushPromises()

    // Now OpenRouter panel is visible
    expect(w.find('[data-action="save-openrouter-key"]').exists()).toBe(true)
    expect(w.find('[data-field="openrouter-model"]').exists()).toBe(true)
    expect(w.text()).toContain('Chave OpenRouter')
    expect(w.text()).toContain('Modelos populares gratuitos')
    w.unmount()
  })

  it('saves OpenRouter API key and clears password input',async()=>{
    const p=props()
    const w=mount(SettingsPanel,{props:p})
    await flushPromises()
    await w.get('#settings-tab-1').trigger('click')
    await w.get('[data-field="provider-openrouter"]').trigger('click')
    await flushPromises()

    const input=w.get('input[type=password]')
    await input.setValue('sk-or-v1-my-secret-key')
    await w.get('[data-action="save-openrouter-key"]').trigger('click')
    await flushPromises()

    expect(p.saveOpenRouterKey).toHaveBeenCalledWith('sk-or-v1-my-secret-key')
    expect((input.element as HTMLInputElement).value).toBe('')
    w.unmount()
  })

  it('selects a free model chip and saves configuration with openrouter',async()=>{
    const p=props({openrouter_key_configured:true})
    const w=mount(SettingsPanel,{props:p})
    await flushPromises()
    await w.get('#settings-tab-1').trigger('click')
    await w.get('[data-field="provider-openrouter"]').trigger('click')
    await flushPromises()

    // Click the Llama 3.3 70B chip
    const chips=w.findAll('.model-chip')
    const llamaChip=chips.find(c=>c.text().includes('Llama 3.3 70B'))
    expect(llamaChip).toBeDefined()
    await llamaChip!.trigger('click')
    await flushPromises()

    expect((w.get('[data-field="openrouter-model"]').element as HTMLInputElement).value).toBe('meta-llama/llama-3.3-70b-instruct:free')

    // Save settings
    await w.get('.settings-main').trigger('submit')
    await flushPromises()

    expect(p.saveConfig).toHaveBeenCalledWith(expect.objectContaining({
      ai_provider:'openrouter',
      openrouter_model:'meta-llama/llama-3.3-70b-instruct:free'
    }))
    w.unmount()
  })
})
