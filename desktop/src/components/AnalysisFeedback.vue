<script setup lang="ts">
import {computed} from 'vue'
import type {Job} from '../types'
import {active,labels} from '../format'
const props=defineProps<{jobs:Job[]}>()
defineEmits<{history:[id:string]}>()
const job=computed(()=>props.jobs.find(j=>['analyze','prepare'].includes(j.operation)&&active(j.status))||props.jobs.find(j=>['analyze','prepare'].includes(j.operation)))
const events=computed(()=>job.value?.events.filter(e=>e?.kind)||[])
const latest=computed(()=>events.value.at(-1))
const context=computed(()=>events.value.filter(e=>e.window_id).at(-1))
const scoped=computed(()=>context.value?events.value.filter(e=>e.window_id===context.value?.window_id&&e.attempt===context.value?.attempt):events.value)
const summary=computed(()=>{
  return scoped.value.filter(e=>e.kind==='thought_summary').map(e=>e.message).join('')
})
const unavailable=computed(()=>scoped.value.filter(e=>['thoughts_unavailable','thoughts_disabled','analysis_cache_reused'].includes(e.kind)).at(-1))
const validated=computed(()=>scoped.value.filter(e=>['window_validated','analysis_cache_reused'].includes(e.kind)).at(-1))
const status=computed(()=>latest.value?.message||(job.value&&active(job.value.status)?'Aguardando feedback da análise.':'Este trabalho não registrou resumos do Gemini.'))
const budgetNotice=computed(()=>{
  const planned=events.value.find(e=>e.kind==='analysis_started')?.windows
  if(job.value?.requests_used===0&&(job.value.error?.code==='PROVIDER_BUDGET'||(planned&&job.value.request_limit!=null&&planned>job.value.request_limit)))return `Limite de ${job.value.request_limit} tentativa(s) insuficiente${planned?' para '+planned+' janelas':''}. Nenhuma solicitação de análise foi enviada. Inicie uma nova análise para usar o planejamento automático de chamadas.`
  return ''
})
</script>
<template>
  <section v-if="job" class="analysis-feedback" aria-label="Análise do Gemini">
    <h4>Análise do Gemini</h4><small v-if="context?.window_index">Janela {{context.window_index}} · tentativa {{context.attempt||job.requests_used}}</small>
    <template v-if="summary"><small class="feedback-origin">Resumo enviado pelo Gemini</small><p class="thought-text">{{summary}}</p></template>
    <p v-else class="feedback-status">{{budgetNotice||unavailable?.message||status}}</p>
    <p v-if="summary&&latest?.kind!=='thought_summary'" class="feedback-status">Aplicativo: {{status}}</p>
    <p v-else-if="!summary&&unavailable&&latest?.id!==unavailable.id" class="feedback-status">Aplicativo: {{status}}</p>
    <p v-if="['failed','cancelled','interrupted'].includes(job.status)" class="feedback-status">{{labels[job.status]}}. {{summary?'Os resumos recebidos são parciais e não representam uma análise completa.':'Este trabalho não completou a análise.'}}</p>
    <ul v-if="validated?.topics?.length" class="feedback-topics"><li v-for="topic in validated.topics.slice(0,2)" :key="topic.id">{{topic.label}}</li></ul>
    <small v-if="validated?.candidates?.length">{{validated.candidates.length}} proposta(s) recebida(s), ainda sem aprovação.</small>
    <button type="button" class="button small secondary" data-action="analysis-history" @click="$emit('history',job.id)">Ver histórico e propostas</button>
    <small>Resumos da API, não o pensamento interno completo. As propostas exigem revisão.</small>
  </section>
</template>
