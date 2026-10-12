import {mount,flushPromises} from '@vue/test-utils'
import {it,expect,vi} from 'vitest'
vi.mock('vue-sonner',()=>({Toaster:{props:['position','closeButton','containerAriaLabel'],template:'<section data-testid="toaster">Avisos</section>'}}))
import AppToaster from '../src/components/AppToaster.vue'
it('keeps one top-center host visible inside a native dialog and returns it to body',async()=>{
 const dialog=document.createElement('dialog');document.body.append(dialog)
 const wrapper=mount(AppToaster,{attachTo:document.body});await flushPromises()
 expect(document.body.querySelectorAll('[data-testid=toaster]')).toHaveLength(1)
 expect(wrapper.html()).toContain('teleport')
 dialog.setAttribute('open','');await flushPromises()
 expect(dialog.querySelector('[data-testid=toaster]')).not.toBeNull()
 expect(document.body.querySelectorAll('[data-testid=toaster]')).toHaveLength(1)
 dialog.removeAttribute('open');await flushPromises()
 expect(dialog.querySelector('[data-testid=toaster]')).toBeNull()
 expect(document.body.querySelectorAll('[data-testid=toaster]')).toHaveLength(1)
 wrapper.unmount();dialog.remove()
})
