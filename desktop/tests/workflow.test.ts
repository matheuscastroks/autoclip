import {mount} from '@vue/test-utils'
import {describe,it,expect} from 'vitest'
import ProjectWorkspace from '../src/components/ProjectWorkspace.vue'
import ProjectLibrary from '../src/components/ProjectLibrary.vue'
const project={id:'p',name:'Teste',title:'Entrevista',path:'/fixture',duration_us:30000000,status:'processing',has_transcript:false,word_count:0,revisions:[],has_analysis:false,is_manual:false,warnings:[],created_at:'',updated_at:0,source:null,error:null}
describe('workflow visibility',()=>{
  it.each(['running','completed'])('does not show an old project error while the current job is %s',status=>{
    const oldFailure={...project,error:{code:'PROVIDER_UNAVAILABLE',message:'Falha antiga'}}
    const w=mount(ProjectWorkspace,{props:{project:oldFailure,transcript:null,revisions:[],jobs:[{id:'j',project_id:'p',operation:'analyze',status,created_at:'',requests_used:1,request_limit:28,events:[]}],sourceUrl:'',previewUrl:'',busy:status==='running'}})
    expect(w.text()).not.toContain('PROVIDER_UNAVAILABLE');w.unmount()
  })
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
  it('does not mark completed or pending stages as failed after an analysis failure',()=>{
    const imported={...project,has_transcript:true,source:{local_path:'/fixture',original_title:'Fixture',channel:'',attribution:'',sha256:'a'.repeat(64)}}
    const w=mount(ProjectWorkspace,{props:{project:imported,transcript:null,revisions:[],jobs:[{id:'j',project_id:'p',operation:'analyze',status:'failed',created_at:'',requests_used:0,request_limit:1,events:[],progress:{stage:'analyze',steps:{import:'pending',transcribe:'pending',analyze:'failed',render:'pending'}}}],sourceUrl:'',previewUrl:'',busy:false}})
    expect(w.get('[data-stage=import]').text()).toContain('Concluído')
    expect(w.get('[data-stage=transcribe]').text()).toContain('Concluído')
    expect(w.get('[data-stage=render]').text()).toContain('Na fila');w.unmount()
  })
})
