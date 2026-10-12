import {mount,flushPromises} from '@vue/test-utils'
import {it,expect,vi} from 'vitest'
vi.mock('../src/api',()=>({api:{projects:vi.fn().mockResolvedValue([]),jobs:vi.fn().mockResolvedValue([]),config:vi.fn().mockResolvedValue({asr_model_path:'/model',gemini_model:'fixture',max_calls:10,window_seconds:600,max_text_chars:60000,ffmpeg:'/ffmpeg',ffprobe:'/probe',asr_available:true,tools_available:true,gemini_key_configured:true}),pick:vi.fn().mockResolvedValue('/fixture.mp4'),create:vi.fn().mockRejectedValue(new Error('Importação de teste recusada.'))}}))
import App from '../src/App.vue'
it('displays an action failure in the single toaster inside the still-open dialog',async()=>{
 vi.stubGlobal('matchMedia',()=>({matches:false,addListener:vi.fn(),removeListener:vi.fn(),addEventListener:vi.fn(),removeEventListener:vi.fn()}))
 HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','')}
 HTMLDialogElement.prototype.close=function(){this.removeAttribute('open')}
 const wrapper=mount(App,{attachTo:document.body});await flushPromises()
 await wrapper.get('.sidebar-create').trigger('click');await flushPromises()
 await wrapper.get('.file-drop button').trigger('click');await flushPromises()
 await wrapper.get('dialog[open] form').trigger('submit');await flushPromises()
 const host=document.querySelector('dialog[open] [data-sonner-toaster]')
 expect(host).not.toBeNull()
 expect(document.querySelectorAll('[data-sonner-toaster]')).toHaveLength(1)
 expect(host?.getAttribute('data-x-position')).toBe('center')
 expect(host?.getAttribute('data-y-position')).toBe('top')
 expect(host?.textContent).toContain('Importação de teste recusada.')
 expect(wrapper.find('.notice').exists()).toBe(false)
 document.dispatchEvent(new KeyboardEvent('keydown',{code:'KeyT',key:'t',altKey:true,bubbles:true}));await flushPromises()
 expect(document.activeElement?.closest('[data-sonner-toaster]')).toBe(host)
 await wrapper.get('dialog[open] button[title=Fechar]').trigger('click');await flushPromises()
 expect(document.querySelector('dialog [data-sonner-toaster]')).toBeNull()
 expect(document.querySelectorAll('[data-sonner-toaster]')).toHaveLength(1)
 wrapper.unmount();vi.unstubAllGlobals()
})
