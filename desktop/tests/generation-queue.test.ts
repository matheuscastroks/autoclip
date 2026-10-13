import {mount} from '@vue/test-utils'
import {it,expect} from 'vitest'
import GenerationQueue from '../src/components/GenerationQueue.vue'
it('does not link a ready job item whose revision was removed',()=>{
 const w=mount(GenerationQueue,{props:{revisions:[],jobs:[{id:'j',project_id:'p',operation:'render',status:'completed',created_at:'',requests_used:0,request_limit:null,events:[],progress:{stage:'render',steps:{},items:[{candidate_id:'c',revision_id:'removed',title:'Excluída',state:'ready',phase:'ready',processed_us:0,total_us:null}]}}]}})
 expect(w.text()).not.toContain('Ver prévia');expect(w.text()).not.toContain('Excluída');w.unmount()
})
it('hides the status rail once all previews are ready',()=>{
 const w=mount(GenerationQueue,{props:{jobs:[],revisions:[{revision_id:'r',candidate_id:'c',title:'Prévia salva',technical_pass:true,review_status:'needs_review',warnings:[]}]}})
 expect(w.find('.generation-queue').exists()).toBe(false);w.unmount()
})
it('keeps running and pending previews above completed ones without changing the snapshot',()=>{
 const items=[{candidate_id:'done',title:'Pronta',state:'ready',phase:'ready',processed_us:0,total_us:null},{candidate_id:'wait',title:'Pendente',state:'waiting',phase:'waiting',processed_us:0,total_us:null},{candidate_id:'active',title:'Ativa',state:'running',phase:'render',processed_us:1,total_us:10}]
 const w=mount(GenerationQueue,{props:{jobs:[{id:'j',project_id:'p',operation:'render',status:'running',created_at:'',requests_used:0,request_limit:null,events:[],progress:{stage:'render',steps:{},items}}]}})
 expect(w.findAll('li').map(li=>li.attributes('data-state'))).toEqual(['running','waiting'])
 expect(items[0].candidate_id).toBe('done');w.unmount()
})
it('shows face tracking progress before encoding',()=>{
 const job={id:'faces',project_id:'p',operation:'render',status:'running',created_at:'',requests_used:0,request_limit:null,events:[],progress:{stage:'render',steps:{},completed_items:0,total_items:1,items:[{candidate_id:'a',title:'Entrevista',state:'running',phase:'reframe',processed_us:50,total_us:100}]}}
 const w=mount(GenerationQueue,{props:{jobs:[job]}})
 expect(w.text()).toContain('Acompanhando rosto')
 expect(w.text()).toContain('50% analisado · Codificação a seguir')
 expect(w.get('[role=progressbar]').attributes('aria-valuenow')).toBe('50')
})
it('distinguishes completed coding from readiness and retries only through the job snapshot',async()=>{
 const job={id:'j',project_id:'p',operation:'render',status:'running',created_at:'',requests_used:0,request_limit:null,events:[],progress:{stage:'render',steps:{},completed_items:1,total_items:3,items:[{candidate_id:'a',title:'Pronta',state:'ready',phase:'ready',processed_us:0,total_us:null},{candidate_id:'b',title:'Codificando',state:'running',phase:'render',processed_us:100,total_us:100},{candidate_id:'c',title:'Falha localizada',state:'failed',phase:'failed',processed_us:0,total_us:null,error_code:'RENDER_FAILED',error_stage:'edit_plan',error_message:'clip would exceed 180s',error_type:'RecutError'}]}}
 const w=mount(GenerationQueue,{props:{jobs:[job]}})
 expect(w.text()).toContain('2 pendente(s)');expect(w.text()).toContain('100% codificado · Verificação técnica a seguir')
 expect(w.find('[data-state=failed]').text()).toContain('outras prévias foram preservadas');expect(w.find('[data-state=failed]').text()).toContain('clip would exceed 180s');expect(w.find('[data-state=failed]').text()).toContain('Preparando edição')
 await w.setProps({jobs:[{...job,status:'failed'}]})
 await w.get('button[aria-label="Tentar novamente: Falha localizada"]').trigger('click')
 expect(w.emitted('retry')?.[0]).toEqual([{job_id:'j',candidate_id:'c'}])
 await w.findAll('button').at(-1)!.trigger('click')
 expect(w.emitted('resume')?.[0]).toEqual(['j'])
})
