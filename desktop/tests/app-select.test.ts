import {mount,flushPromises} from '@vue/test-utils'
import {describe,it,expect,vi} from 'vitest'
import AppSelect from '../src/components/AppSelect.vue'
const options=[{value:'a',label:'Primeiro'},{value:'b',label:'Segundo'},{value:'c',label:'Indisponível',disabled:true}]
describe('brutalist select',()=>{
 it('uses a custom trigger and preserves the selected exact value',()=>{
  const w=mount(AppSelect,{props:{modelValue:'b',options,label:'Modelo'}})
  expect(w.get('[role=combobox]').text()).toContain('Segundo')
  expect(w.find('select:not([aria-hidden])').exists()).toBe(false);w.unmount()
 })
 it('opens with the keyboard and marks disabled options',async()=>{
  const w=mount(AppSelect,{attachTo:document.body,props:{modelValue:'a',options,label:'Modelo'}})
  await w.get('[role=combobox]').trigger('keydown',{key:'ArrowDown'});await flushPromises()
  expect(document.querySelector('[role=listbox]')).not.toBeNull()
  expect(document.querySelector('[role=option][data-disabled]')?.textContent).toContain('Indisponível')
  const item=document.querySelectorAll<HTMLElement>('[role=option]')[1]!;item.focus();item.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}));await flushPromises()
  expect(w.emitted('update:modelValue')?.[0]).toEqual(['b']);w.unmount()
 })
 it('does not open a disabled control',async()=>{
  const w=mount(AppSelect,{props:{modelValue:'a',options,label:'Modelo',disabled:true}})
  expect((w.get('button').element as HTMLButtonElement).disabled).toBe(true);w.unmount()
 })
})
