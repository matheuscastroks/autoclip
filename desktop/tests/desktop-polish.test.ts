import {mount} from '@vue/test-utils'
import {describe,it,expect,vi} from 'vitest'
import AppButton from '../src/components/AppButton.vue'
import ProjectLibrary from '../src/components/ProjectLibrary.vue'
import SettingsPanel from '../src/components/SettingsPanel.vue'
describe('desktop controls',()=>{
  it('forwards native attributes and emits one click',async()=>{
    const click=vi.fn();const w=mount(AppButton,{attrs:{type:'submit','aria-label':'Salvar',onClick:click}})
    expect(w.get('button').attributes('type')).toBe('submit');await w.trigger('click');expect(click).toHaveBeenCalledTimes(1)
  })
  it('shows unique summary counts and sorts by latest update',async()=>{
    const base={name:'Projeto',path:'',status:'analyzed',duration_us:1,has_transcript:true,has_analysis:true,word_count:1,is_manual:false,revisions:[],warnings:[],created_at:'',source:null,error:null}
    const w=mount(ProjectLibrary,{props:{busy:false,projects:[{...base,id:'a',title:'Antigo',updated_at:1},{...base,id:'b',title:'Atual',updated_at:2,summary:{proposed:4,selected:2,generated:1,stage:'analyze'}}]}})
    expect(w.findAll('[data-project-id]')[0].attributes('data-project-id')).toBe('b')
    expect(w.text()).toContain('4 propostas');expect(w.text()).toContain('2 selecionados')
  })
  it('puts connection before model choice and saves a key with Enter',async()=>{
    const save=vi.fn().mockResolvedValue(undefined)
    const w=mount(SettingsPanel,{props:{config:{asr_model_path:'m',gemini_model:'g',max_calls:0,window_seconds:600,max_text_chars:60000,ffmpeg:'f',ffprobe:'p',asr_available:true,tools_available:true,gemini_key_configured:false},saveConfig:vi.fn(),saveKey:save,pick:vi.fn()}})
    expect(w.text().indexOf('Chave Gemini')).toBeLessThan(w.text().indexOf('Seleção de trechos'))
    await w.get('input[type=password]').setValue('fixture-key');await w.get('input[type=password]').trigger('keydown',{key:'Enter'})
    expect(save).toHaveBeenCalledWith('fixture-key')
  })
})
