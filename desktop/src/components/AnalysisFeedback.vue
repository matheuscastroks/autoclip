<script setup lang="ts">
import AppButton from './AppButton.vue'
import {computed,ref,watch,nextTick} from 'vue'
import type {Job,AnalysisEvent} from '../types'
import {active,labels,latestJob} from '../format'
const props=defineProps<{jobs:Job[]}>()
const job=computed(()=>latestJob(props.jobs.filter(j=>['analyze','prepare'].includes(j.operation))))
const events=ref<AnalysisEvent[]>([]),scrollArea=ref<HTMLElement>(),following=ref(true)
let retainedJob=''
watch(job,current=>{
  if(current?.id!==retainedJob){retainedJob=current?.id||'';events.value=[];following.value=true}
  // Polling returns a bounded tail. Keep already received chunks instead of erasing them.
  const received=new Map(events.value.map(e=>[e.id,e]))
  for(const event of current?.events||[])if(event?.kind)received.set(event.id,event)
  events.value=[...received.values()].slice(-2000)
},{immediate:true})
const latest=computed(()=>events.value.at(-1))
const context=computed(()=>events.value.filter(e=>e.window_id).at(-1))
const scoped=computed(()=>context.value?events.value.filter(e=>e.window_id===context.value?.window_id&&e.attempt===context.value?.attempt):events.value)
const summary=computed(()=>{
  return scoped.value.filter(e=>e.kind==='thought_summary').map(e=>e.message).join('')
})
const unavailable=computed(()=>scoped.value.filter(e=>['thoughts_unavailable','thoughts_disabled','analysis_cache_reused'].includes(e.kind)).at(-1))
const validated=computed(()=>scoped.value.filter(e=>['window_validated','analysis_cache_reused'].includes(e.kind)).at(-1))
const status=computed(()=>latest.value?.message||(job.value&&active(job.value.status)?'Aguardando feedback da análise.':'Este trabalho não registrou resumos da IA.'))
const budgetNotice=computed(()=>{
  const planned=events.value.find(e=>e.kind==='analysis_started')?.windows
  if(job.value?.requests_used===0&&(job.value.error?.code==='PROVIDER_BUDGET'||(planned&&job.value.request_limit!=null&&planned>job.value.request_limit)))return `Limite de ${job.value.request_limit} tentativa(s) insuficiente${planned?' para '+planned+' janelas':''}. Nenhuma solicitação de análise foi enviada. Inicie uma nova análise para usar o planejamento automático de chamadas.`
  return ''
})
watch(summary,async()=>{await nextTick();if(following.value&&scrollArea.value)scrollArea.value.scrollTop=scrollArea.value.scrollHeight},{immediate:true})
function onScroll(){if(scrollArea.value&&scrollArea.value.scrollHeight-scrollArea.value.clientHeight-scrollArea.value.scrollTop>32)following.value=false}
async function toggleFollow(){following.value=!following.value;await nextTick();if(following.value&&scrollArea.value)scrollArea.value.scrollTop=scrollArea.value.scrollHeight}
</script>
<template>
  <section v-if="job" class="analysis-feedback" aria-label="Análise de IA">
    <div class="feedback-heading">
      <h4>Análise de IA</h4>
      <el-tag
        size="small"
        :type="job.status==='completed'?'success':job.status==='failed'?'danger':active(job.status)?'primary':'info'"
        effect="dark"
        class="feedback-state"
        role="status"
      >
        {{labels[job.status]||job.status}}
      </el-tag>
    </div>
    <small v-if="context?.window_index">Janela {{context.window_index}} · {{context.attempt===0?'resultado reaproveitado':'tentativa '+(context.attempt||job.requests_used)}}</small>
    <template v-if="summary"><div class="summary-toolbar"><small class="feedback-origin">Resumo enviado pelo Gemini</small><AppButton type="button" class="text-button" data-action="toggle-follow" :aria-pressed="following" @click="toggleFollow">{{following?'Pausar acompanhamento':'Acompanhar atualizações'}}</AppButton></div><div ref="scrollArea" class="thought-scroll hidden-scrollbar" role="region" aria-label="Resumo da análise atual" tabindex="0" @scroll="onScroll"><p class="thought-text">{{summary}}</p></div></template>
    <p v-else class="feedback-status">{{budgetNotice||unavailable?.message||status}}</p>
    <p v-if="summary&&latest?.kind!=='thought_summary'" class="feedback-status">Aplicativo: {{status}}</p>
    <p v-else-if="!summary&&unavailable&&latest?.id!==unavailable.id" class="feedback-status">Aplicativo: {{status}}</p>
    <p v-if="['failed','cancelled','interrupted'].includes(job.status)" class="feedback-status">{{labels[job.status]}}. {{summary?'Os resumos recebidos são parciais e não representam uma análise completa.':'Este trabalho não completou a análise.'}}</p>
    <ul v-if="validated?.topics?.length" class="feedback-topics"><li v-for="topic in validated.topics.slice(0,2)" :key="topic.id">{{topic.label}}</li></ul>
    <small v-if="validated?.candidates?.length">{{validated.candidates.length}} proposta(s) recebida(s), ainda sem aprovação.</small>
    <small>Resumos da API, não o pensamento interno completo. As propostas exigem revisão.</small>
  </section>
</template>
