import {mount,flushPromises} from '@vue/test-utils'
import {it,expect,vi} from 'vitest'

const mockNotification = vi.fn()
vi.mock('element-plus', async (importOriginal) => {
  const actual = await importOriginal<typeof import('element-plus')>()
  return {
    ...actual,
    ElNotification: (...args: unknown[]) => mockNotification(...args),
  }
})

vi.mock('../src/api',()=>({api:{projects:vi.fn().mockResolvedValue([]),jobs:vi.fn().mockResolvedValue([]),config:vi.fn().mockResolvedValue({asr_model_path:'/model',gemini_model:'fixture',max_calls:10,window_seconds:600,max_text_chars:60000,ffmpeg:'/ffmpeg',ffprobe:'/probe',asr_available:true,tools_available:true,gemini_key_configured:true}),pick:vi.fn().mockResolvedValue('/fixture.mp4'),create:vi.fn().mockRejectedValue(new Error('Importação de teste recusada.'))}}))
import App from '../src/App.vue'

it('dispatches error notification when project creation fails inside dialog',async()=>{
 vi.stubGlobal('matchMedia',()=>({matches:false,addListener:vi.fn(),removeListener:vi.fn(),addEventListener:vi.fn(),removeEventListener:vi.fn()}))
 HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','')}
 HTMLDialogElement.prototype.close=function(){this.removeAttribute('open')}
 const wrapper=mount(App,{attachTo:document.body});await flushPromises()
 await wrapper.get('.new-project-action').trigger('click');await flushPromises()
 await wrapper.get('.file-drop button').trigger('click');await flushPromises()
 await wrapper.get('dialog[open] form').trigger('submit');await flushPromises()

 expect(mockNotification).toHaveBeenCalledWith(expect.objectContaining({
   type: 'error',
   message: expect.stringContaining('Importação de teste recusada.')
 }))

 await wrapper.get('dialog[open] button[title=Fechar]').trigger('click');await flushPromises()
 wrapper.unmount();vi.unstubAllGlobals()
})
