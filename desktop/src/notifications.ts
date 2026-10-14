import {ElNotification} from 'element-plus'
import type {Job} from './types'

type Options={key?:string;description?:string;force?:boolean}
const seen=new Set<string>()

function send(kind:'error'|'success'|'warning'|'info',message:string,options:Options={}){
  if(!message)return
  if(options.key&&!options.force&&seen.has(options.key))return
  if(options.key){
    seen.add(options.key)
    if(seen.size>500)seen.delete(seen.values().next().value!)
  }
  return ElNotification({
    title: kind==='error'?'Erro':kind==='warning'?'Atenção':kind==='success'?'Sucesso':'Informação',
    message: options.description ? `${message} · ${options.description}` : message,
    type: kind,
    duration: kind==='error'?9000:kind==='warning'?7000:4500,
    position: 'top-right',
    customClass: 'studio-notification'
  })
}

export const notify={
  error:(message:string,options?:Options)=>send('error',message,options),
  success:(message:string,options?:Options)=>send('success',message,options),
  warning:(message:string,options?:Options)=>send('warning',message,options),
  info:(message:string,options?:Options)=>send('info',message,options)
}

export function resetNotifications(){seen.clear()}

export function notifyJob(job:Job,force=false){
  const key=`job:${job.id}:${job.status}`
  if(job.status==='failed'||job.status==='interrupted')notify.error(job.operation==='prepare'||job.operation==='import'?'A preparação precisa de atenção':'A tarefa precisa de atenção',{key,force,description:job.error?.message||'A tarefa foi interrompida. Você pode continuar pelo projeto.'})
  else if(job.status==='cancelled')notify.info('Tarefa cancelada',{key,force,description:'Os resultados já concluídos foram preservados.'})
  else if(job.status==='completed')notify.success(job.operation==='render'?'Prévias prontas para revisão':job.operation==='export'?'Exportação concluída':job.operation==='import'?'Vídeo importado':job.operation==='transcribe'?'Transcrição concluída':'Análise concluída',{key,force})
}

export function createJobNotifier(){
  let initialized=false
  const states=new Map<string,string>()
  const failedItems=new Set<string>()
  return (jobs:Job[])=>{
    for(const job of jobs){
      if(initialized&&states.get(job.id)!==job.status)notifyJob(job)
      for(const item of job.progress?.items||[]){
        if(item.state!=='failed')continue
        const key=`item:${job.id}:${item.candidate_id}`
        if(initialized&&!failedItems.has(key))notify.error('Não foi possível gerar esta prévia',{key,description:`${item.title} · ${item.error_code||'Falha na geração'}. As prévias prontas foram preservadas.`})
        failedItems.add(key)
      }
      states.set(job.id,job.status)
    }
    initialized=true
  }
}
