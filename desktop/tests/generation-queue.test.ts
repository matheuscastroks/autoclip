import {mount} from '@vue/test-utils'
import {it,expect} from 'vitest'
import GenerationQueue from '../src/components/GenerationQueue.vue'
it('distinguishes completed coding from readiness and retries only through the job snapshot',async()=>{
 const job={id:'j',project_id:'p',operation:'render',status:'running',created_at:'',requests_used:0,request_limit:null,events:[],progress:{stage:'render',steps:{},completed_items:1,total_items:3,items:[{candidate_id:'a',title:'Pronta',state:'ready',phase:'ready',processed_us:0,total_us:null},{candidate_id:'b',title:'Codificando',state:'running',phase:'render',processed_us:100,total_us:100},{candidate_id:'c',title:'Falha localizada',state:'failed',phase:'failed',processed_us:0,total_us:null,error_code:'RENDER_FAILED'}]}}
 const w=mount(GenerationQueue,{props:{jobs:[job]}})
 expect(w.text()).toContain('1/3 prontas');expect(w.text()).toContain('100% codificado · Verificação técnica a seguir')
 expect(w.find('[data-state=failed]').text()).toContain('outras prévias foram preservadas')
 await w.setProps({jobs:[{...job,status:'failed'}]});await w.get('button').trigger('click')
 expect(w.emitted('resume')?.[0]).toEqual(['j'])
})
