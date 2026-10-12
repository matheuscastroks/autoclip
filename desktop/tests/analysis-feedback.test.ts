import {mount,flushPromises} from '@vue/test-utils'
import {describe,it,expect,vi} from 'vitest'
import SettingsPanel from '../src/components/SettingsPanel.vue'
import AnalysisFeedback from '../src/components/AnalysisFeedback.vue'
const config={asr_model_path:'/model',gemini_model:'fixture',max_calls:3,window_seconds:600,max_text_chars:60000,ffmpeg:'/ffmpeg',ffprobe:'/probe',asr_available:true,tools_available:true,gemini_key_configured:true}
describe('editorial controls and Gemini feedback',()=>{
  it('saves duration, pause policy and summary visibility from settings',async()=>{
    const save=vi.fn().mockResolvedValue({});const w=mount(SettingsPanel,{props:{config,saveConfig:save,saveKey:vi.fn(),pick:vi.fn()}})
    await w.get('[data-field=clip-preferred]').setValue(90)
    await w.get('[data-field=clip-max]').setValue(180)
    await w.get('[data-field=pause-mode]').setValue('conservative')
    await w.get('[data-field=thought-summaries]').setValue(true)
    await w.get('.settings-main').trigger('submit');await flushPromises()
    expect(save).toHaveBeenCalledWith(expect.objectContaining({clip_preferred_seconds:90,clip_max_seconds:180,pause_mode:'conservative',show_thought_summaries:true}));w.unmount()
  })
  it('renders actual summary text safely and separates application events',async()=>{
    const job={id:'j',project_id:'p',operation:'analyze',status:'running',created_at:'',request_limit:3,requests_used:1,events:[{id:'1',at:'',kind:'request_started',message:'Solicitação enviada.',attempt:1},{id:'2',at:'',kind:'thought_summary',message:'<img src=x onerror=alert(1)> Conferindo a conclusão.',attempt:1,window_id:'w1'}]}
    const w=mount(AnalysisFeedback,{props:{jobs:[job]}})
    expect(w.text()).toContain('Conferindo a conclusão')
    expect(w.find('img').exists()).toBe(false)
    expect(w.text()).toContain('Resumo enviado pelo Gemini')
    await w.get('[data-action=analysis-history]').trigger('click')
    expect(w.emitted('history')?.[0]).toEqual(['j']);w.unmount()
  })
  it('does not invent thinking when the provider has no summary',()=>{
    const w=mount(AnalysisFeedback,{props:{jobs:[{id:'j',project_id:'p',operation:'analyze',status:'completed',created_at:'',request_limit:3,requests_used:1,events:[{id:'1',at:'',kind:'thoughts_unavailable',message:'Gemini não forneceu resumos nesta tentativa.'}]}]}})
    expect(w.text()).toContain('não forneceu resumos');expect(w.find('.thought-text').exists()).toBe(false);w.unmount()
  })
  it('does not show an earlier attempt summary as the current attempt',()=>{
    const w=mount(AnalysisFeedback,{props:{jobs:[{id:'j',project_id:'p',operation:'analyze',status:'running',created_at:'',request_limit:3,requests_used:2,events:[{id:'1',at:'',kind:'thought_summary',message:'Resumo antigo.',window_id:'w1',attempt:1},{id:'2',at:'',kind:'request_started',message:'Aguardando segunda tentativa.',window_id:'w1',attempt:2}]}]}})
    expect(w.text()).not.toContain('Resumo antigo.');expect(w.text()).toContain('Aguardando segunda tentativa.');w.unmount()
  })
  it('labels summaries as partial after forced cancellation',()=>{
    const w=mount(AnalysisFeedback,{props:{jobs:[{id:'j',project_id:'p',operation:'analyze',status:'cancelled',created_at:'',request_limit:3,requests_used:1,events:[{id:'1',at:'',kind:'thought_summary',message:'Examinando a conclusão.',window_id:'w1',attempt:1}]}]}})
    expect(w.text()).toContain('parciais');expect(w.text()).toContain('Cancelado');w.unmount()
  })
  it('explains an insufficient budget without inventing provider activity',()=>{
    const w=mount(AnalysisFeedback,{props:{jobs:[{id:'j',project_id:'p',operation:'analyze',status:'failed',created_at:'',request_limit:1,requests_used:0,error:{code:'PROVIDER_BUDGET',message:'Limite insuficiente'},events:[{id:'1',at:'',kind:'analysis_started',message:'Planejando as janelas.',windows:3}]}]}})
    expect(w.text()).toContain('3 janelas');expect(w.text()).toContain('Nenhuma solicitação');w.unmount()
  })
})
