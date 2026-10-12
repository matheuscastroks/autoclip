import {mount,flushPromises} from '@vue/test-utils'
import {describe,it,expect,vi,afterEach} from 'vitest'
import App from '../src/App.vue'
import {api} from '../src/api'
afterEach(()=>vi.restoreAllMocks())
const project={id:'p',name:'Projeto fixture',title:'Vídeo fixture',path:'/fixture',duration_us:30000000,status:'needs_review',has_transcript:true,word_count:1,revisions:[],has_analysis:true,is_manual:false,warnings:[],created_at:'',updated_at:0,source:{local_path:'/fixture.mp4',original_title:'Fixture',channel:'',attribution:'TEST ONLY',sha256:'a'.repeat(64)},error:null}
const config={asr_model_path:'/model',gemini_model:'fixture',max_calls:1,window_seconds:600,max_text_chars:60000,ffmpeg:'/ffmpeg',ffprobe:'/probe',asr_available:true,tools_available:true,gemini_key_configured:false}
const revisions=['A','B'].map(id=>({revision_id:id,title:'Corte '+id,rationale:'TEST ONLY',technical_pass:true,review_status:'needs_review',duration_us:20000000,start_us:0,end_us:20000000,caption_words:[],warnings:[],content_hash:'a'.repeat(64)}))
function setup(){
  vi.spyOn(api,'projects').mockResolvedValue([project]);vi.spyOn(api,'project').mockResolvedValue(project)
  vi.spyOn(api,'config').mockResolvedValue(config);vi.spyOn(api,'jobs').mockResolvedValue([])
  vi.spyOn(api,'transcript').mockResolvedValue({words:[{id:'w',text:'Texto fixture',start_us:0,end_us:1000000}],segments:[]})
  vi.spyOn(api,'revisions').mockResolvedValue(revisions);vi.spyOn(api,'media').mockImplementation(async (_pid,asset)=>'/media/'+asset)
  vi.spyOn(api,'decide').mockResolvedValue({})
}
async function open(){const w=mount(App);await flushPromises();await w.get('[data-project-id=p]').trigger('click');await flushPromises();return w}
describe('review identity across refresh and failures',()=>{
  it('loads original as soon as automatic import finishes while the job is still running',async()=>{
    setup()
    const pending={...project,source:null,has_transcript:false,has_analysis:false,status:'pending_import'}
    vi.mocked(api.projects).mockResolvedValue([pending]);vi.mocked(api.project).mockResolvedValue(pending)
    vi.mocked(api.revisions).mockResolvedValue([])
    vi.mocked(api.jobs).mockResolvedValue([{id:'j',project_id:'p',operation:'prepare',status:'running',created_at:'',requests_used:0,request_limit:2,events:[]}])
    const w=await open();expect(w.find('video').exists()).toBe(false)
    const imported={...pending,source:project.source,status:'processing'}
    vi.mocked(api.projects).mockResolvedValue([imported]);vi.mocked(api.project).mockResolvedValue(imported)
    await w.get('[title="Atualizar projetos"]').trigger('click');await flushPromises()
    expect(w.get('video').attributes('src')).toBe('/media/source');w.unmount()
  })
  it('preserves selected B video and target after a review refresh',async()=>{
    setup();const w=await open();await w.get('[role=tablist] button:nth-child(3)').trigger('click');await flushPromises()
    await w.findAll('.clip-item')[1].trigger('click');await flushPromises()
    expect(w.get('.clip-preview > video').attributes('src')).toBe('/media/B')
    for(const checkbox of w.findAll('.review-checks input[type=checkbox]'))await checkbox.setValue(true)
    await w.get('[data-action=approve]').trigger('click');await flushPromises()
    expect(api.decide).toHaveBeenCalledWith('p',expect.objectContaining({revision_id:'B'}))
    expect(w.get('.clip-preview > video').attributes('src')).toBe('/media/B')
    expect(w.get('.clip-item.selected').text()).toContain('Corte B');w.unmount()
  })
  it('ignores stale media responses when rapidly selecting A then B',async()=>{
    setup();const w=await open();await w.get('[role=tablist] button:nth-child(3)').trigger('click');await flushPromises()
    let resolveA:(value:string)=>void=()=>{},resolveB:(value:string)=>void=()=>{}
    vi.mocked(api.media).mockImplementation((_p,asset)=>new Promise(resolve=>{if(asset==='A')resolveA=resolve;else resolveB=resolve}))
    await w.findAll('.clip-item')[0].trigger('click');await w.findAll('.clip-item')[1].trigger('click')
    resolveB('/media/B');await flushPromises();resolveA('/media/A');await flushPromises()
    expect(w.get('.clip-preview > video').attributes('src')).toBe('/media/B');w.unmount()
  })
  it('keeps transcript and original when revisions endpoint fails',async()=>{
    setup();vi.mocked(api.revisions).mockRejectedValue(new Error('Preview damaged'))
    const w=await open();expect(w.find('video').attributes('src')).toBe('/media/source')
    await w.get('[role=tablist] button:nth-child(2)').trigger('click');await flushPromises()
    expect(w.text()).toContain('Texto fixture');w.unmount()
  })
})
