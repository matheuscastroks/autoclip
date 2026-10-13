import {mount,flushPromises} from '@vue/test-utils'
import {it,expect,vi} from 'vitest'
vi.mock('../src/api',()=>({api:{projects:vi.fn().mockResolvedValue([]),jobs:vi.fn().mockResolvedValue([{id:'other',status:'running'}]),config:vi.fn().mockResolvedValue({}),pick:vi.fn(),create:vi.fn(),importProject:vi.fn()}}))
import ProjectQueue from '../src/components/ProjectQueue.vue'
import App from '../src/App.vue'
import {latestJob} from '../src/format'

it('shows stage, queue position and removal independently of current tab',async()=>{
 const w=mount(ProjectQueue,{props:{busy:false,jobs:[{id:'a',project_id:'p',operation:'transcribe',stage:'transcribe',status:'running',created_at:'1',requests_used:0,request_limit:null,events:[]},{id:'b',project_id:'p',operation:'render',status:'pending',created_at:'2',queue_position:1,queue_reason:'Aguardando a tarefa anterior deste projeto.',requests_used:0,request_limit:null,events:[]}]}})
 expect(w.text()).toContain('1 em execução · 1 aguardando')
 expect(w.text()).toContain('posição 1');expect(w.text()).toContain('Aguardando a tarefa anterior')
 await w.findAll('button')[1].trigger('click');expect(w.emitted('cancel')?.[0]).toEqual(['b'])
 w.unmount()
})
it('allows creating and importing another project while work is active',async()=>{
 const w=mount(App)
 await flushPromises()
 expect(w.get('.new-project-action').attributes('disabled')).toBeUndefined()
 expect(w.get('.header-import-action').attributes('disabled')).toBeUndefined()
 w.unmount()
})
it('keeps running progress in focus when a newer job is queued',()=>{
 expect(latestJob([{id:'running',created_at:'1',status:'running'},{id:'queued',created_at:'2',status:'pending'}] as any)?.id).toBe('running')
})
