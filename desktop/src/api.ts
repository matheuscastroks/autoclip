import type {Project,Config,Job,Revision,Transcript,Decision,GeminiConnection} from './types'
let token=''
export function initializeSession(){
  token=new URLSearchParams(location.hash.slice(1)).get('session')||''
  if(location.hash)history.replaceState(null,'',location.pathname+location.search)
}
export async function request<T>(path:string,options:RequestInit={}):Promise<T>{
  const response=await fetch('/api/v1'+path,{...options,headers:{'Content-Type':'application/json','Authorization':'Bearer '+token,...options.headers}})
  const data=await response.json().catch(()=>({detail:'Resposta local indisponível.'}))
  if(!response.ok){
    const detail=data.detail
    throw new Error(typeof detail==='string'?detail:detail?.code?`${detail.code}: ${detail.message}`:'Não foi possível concluir a operação.')
  }
  return data as T
}
const post=<T>(path:string,body?:unknown)=>request<T>(path,{method:'POST',...(body!==undefined?{body:JSON.stringify(body)}:{})})
export const api={
  projects:()=>request<Project[]>('/projects'),project:(id:string)=>request<Project>('/projects/'+id),
  config:()=>request<Config>('/config'),jobs:()=>request<Job[]>('/jobs'),
  transcript:(id:string)=>request<Transcript>(`/projects/${id}/transcript`),
  revisions:(id:string)=>request<Revision[]>(`/projects/${id}/revisions`),
  media:async(id:string,asset:string)=>(await request<{url:string}>(`/projects/${id}/media/${asset}/ticket`)).url,
  importProject:(path:string)=>post<Project>('/projects/import',{path}),
  create:(name:string,source_input:string)=>post<{project:Project;job:Job}>('/projects',{name,source_input}),
  start:(id:string,operation:string,options:Record<string,unknown>={})=>post<Job>(`/projects/${id}/jobs`,{operation,options}),
  cancel:(id:string)=>post<Job>(`/jobs/${id}/cancel`),resume:(id:string)=>post<Job>(`/jobs/${id}/resume`),
  pick:async(kind:string)=>(await post<{path:string|null}>('/picker',{kind})).path,
  saveConfig:(config:Config)=>request<Config>('/config',{method:'PUT',body:JSON.stringify(Object.fromEntries(Object.entries(config).filter(([k])=>!['schema_version','asr_available','tools_available','gemini_key_configured'].includes(k))))}),
  saveKey:(key:string)=>request<GeminiConnection>('/config/credential',{method:'PUT',body:JSON.stringify({key})}),
  geminiConnection:()=>request<GeminiConnection>('/config/gemini'),
  testGemini:()=>post<GeminiConnection>('/config/gemini/test'),
  decide:(id:string,decision:Decision)=>post(`/projects/${id}/revisions/${decision.revision_id}/decision`,{decision:decision.decision,checks:decision.checks,notes:decision.notes,content_hash:decision.content_hash}),
  openFolder:(id:string)=>post(`/projects/${id}/open-folder`),shutdown:()=>post('/shutdown')
}
