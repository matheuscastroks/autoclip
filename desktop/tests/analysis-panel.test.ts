import {mount} from '@vue/test-utils'
import {it,expect} from 'vitest'
import AnalysisPanel from '../src/components/AnalysisPanel.vue'
const proposal={candidate_id:'one',topic_ids:['t'],group_id:'tema',title:'O argumento completo',rationale:'Mantém a conclusão.',start_us:1000000,end_us:61000000,duration_us:60000000,start_word_id:'w1',end_word_id:'w2',evidence_word_ids:['w1'],editorial:{completeness:'yes'},warnings:[],eligible:true,reasons:[],text:'Fala original.',context_before:'Antes.',context_after:'Depois.'}
const view={schema_version:'1.0',state:'completed',job_id:null,analysis_hash:'a'.repeat(64),model:'fixture',completed_windows:2,total_windows:2,topic_groups:[{id:'tema',label:'Tema',topic_ids:['t'],summaries:['Resumo'],evidence_word_ids:['w1']}],proposals:[proposal,{...proposal,candidate_id:'two',eligible:false,reasons:['editorial flags require review']}]}
it('selects and removes the inspected proposal through the final step',async()=>{
 const w=mount(AnalysisPanel,{props:{analysis:view,selection:null,jobs:[],sourceUrl:'',busy:false}})
 await w.get('[data-action=select-focused]').trigger('click');expect(w.emitted('selection')?.[0]?.[0]).toMatchObject({candidate_ids:['one']})
 await w.get('[data-action=select-focused]').trigger('click');expect(w.emitted('selection')?.[1]?.[0]).toMatchObject({candidate_ids:[]});w.unmount()
})
it('shows a distinct social opening before generation',()=>{
 const w=mount(AnalysisPanel,{props:{analysis:{...view,proposals:[{...proposal,title:'Por que essa ressalva muda tudo',opening_text:'Uma palavra muda o sentido?'}]},selection:null,jobs:[],sourceUrl:'',busy:false}})
 expect(w.get('.proposal-detail h3').text()).toBe('Por que essa ressalva muda tudo')
 expect(w.get('.opening-copy').text()).toContain('Uma palavra muda o sentido?')
 expect(w.get('.opening-copy').text()).toContain('7 segundos')
 w.unmount()
})
it('generates only explicit eligible proposals and preserves selection on polling',async()=>{
 const w=mount(AnalysisPanel,{props:{analysis:view,selection:null,jobs:[],sourceUrl:'',busy:false}})
 const boxes=w.findAll('input[type=checkbox]');expect(boxes[1].attributes('disabled')).toBeDefined()
 await boxes[0].setValue(true);await w.setProps({analysis:structuredClone(view)})
 await w.get('[data-action=generate-selected]').trigger('click')
 expect(w.emitted('generate')?.[0]?.[0]).toEqual({analysis_hash:view.analysis_hash,candidate_ids:['one']})
})
it('shows validated partial data without allowing generation',()=>{
 const w=mount(AnalysisPanel,{props:{analysis:{...view,state:'partial',analysis_hash:null},selection:null,jobs:[],sourceUrl:'',busy:false}})
 expect(w.text()).toContain('parcial');expect(w.get('[data-action=generate-selected]').attributes('disabled')).toBeDefined()
})
it('keeps the topic and inspected proposal when partial analysis completes',async()=>{
 const other={...proposal,candidate_id:'other',title:'Outra proposta'}
 const partial={...view,state:'partial',analysis_hash:null,proposals:[proposal,other]}
 const w=mount(AnalysisPanel,{props:{analysis:partial,selection:null,jobs:[],sourceUrl:'',busy:false}})
 await w.findAll('.topic-list button')[1].trigger('click');await w.findAll('.proposal-open')[1].trigger('click')
 await w.setProps({analysis:{...partial,state:'completed',analysis_hash:view.analysis_hash}})
 expect(w.get('.proposal-detail h3').text()).toBe('Outra proposta')
 expect(w.get('.topic-list button.selected').text()).toContain('Tema')
})
it('distinguishes failed analysis from not started and offers no synthetic selection',()=>{
 const w=mount(AnalysisPanel,{props:{analysis:{...view,state:'failed',model:null,analysis_hash:null,proposals:[],topic_groups:[]},selection:null,jobs:[],sourceUrl:'',busy:false}})
 expect(w.get('.analysis-heading').text()).toContain('Análise precisa de atenção')
 expect(w.get('.analysis-heading').text()).not.toContain('Análise ainda não iniciada')
 expect(w.find('[data-action=select-focused]').exists()).toBe(false)
 expect(w.get('.proposal-empty').text()).toContain('Os trechos aparecerão aqui')
 expect(w.get('[data-action=generate-selected]').attributes('disabled')).toBeDefined()
 w.unmount()
})
