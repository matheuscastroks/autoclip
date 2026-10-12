import {mount} from '@vue/test-utils'
import {describe,it,expect} from 'vitest'
import ProjectWorkspace from '../src/components/ProjectWorkspace.vue'
import ProjectLibrary from '../src/components/ProjectLibrary.vue'
const project={id:'p',name:'Teste',title:'Entrevista',path:'/fixture',duration_us:30000000,status:'processing',has_transcript:false,word_count:0,revisions:[],has_analysis:false,is_manual:false,warnings:[],created_at:'',updated_at:0,source:null,error:null}
describe('workflow visibility',()=>{
  it('keeps stage activity and cancellation beside the video',()=>{
    const w=mount(ProjectWorkspace,{props:{project,transcript:null,revisions:[],jobs:[{id:'j',project_id:'p',operation:'prepare',status:'running',created_at:'',requests_used:0,request_limit:10,events:[],progress:{stage:'transcribe',steps:{import:'completed',transcribe:'running',analyze:'pending',render:'pending'}}}],sourceUrl:'',previewUrl:'',busy:true}})
    expect(w.get('.pipeline-panel [data-stage=transcribe] [role=progressbar]').attributes('aria-label')).toContain('Transcrever')
    expect(w.get('.pipeline-panel').text()).toContain('Cancelar')
    expect(w.find('.project-jobs').exists()).toBe(false)
  })
  it('uses actual covers and provides project deletion without opening it',async()=>{
    const w=mount(ProjectLibrary,{props:{projects:[project],busy:false,covers:{p:'/thumbnail.jpg'}}})
    expect(w.get('img').attributes('src')).toBe('/thumbnail.jpg')
    await w.get('[data-action=delete-project]').trigger('click')
    expect(w.emitted('delete')?.[0]).toEqual(['p'])
    expect(w.emitted('open')).toBeUndefined()
  })
  it('stops an animated bar when the worker was forcibly cancelled',()=>{
    const w=mount(ProjectWorkspace,{props:{project,transcript:null,revisions:[],jobs:[{id:'j',project_id:'p',operation:'prepare',status:'cancelled',created_at:'',requests_used:0,request_limit:10,events:[],progress:{stage:'transcribe',steps:{import:'completed',transcribe:'running',analyze:'pending',render:'pending'}}}],sourceUrl:'',previewUrl:'',busy:false}})
    expect(w.get('[data-stage=transcribe]').text()).toContain('Cancelado')
    expect(w.get('[data-stage=transcribe] .stage-progress').classes()).not.toContain('indeterminate')
  })
})
