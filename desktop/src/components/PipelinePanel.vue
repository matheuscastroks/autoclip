<script setup lang="ts">
import {computed} from 'vue'
import {Check,Square,RotateCcw} from '@lucide/vue'
import type {Project,Job} from '../types'
import {active,labels} from '../format'
const props=defineProps<{project:Project;jobs:Job[];busy:boolean;hasCuts:boolean}>()
defineEmits<{transcribe:[];analyze:[];render:[];review:[];cancel:[id:string];resume:[id:string]}>()
const names=[['import','Importar vídeo'],['transcribe','Transcrever'],['analyze','Analisar temas'],['render','Gerar e revisar']] as const
const job=computed(()=>props.jobs.find(j=>active(j.status))||props.jobs[0])
const processing=computed(()=>props.jobs.some(j=>active(j.status)))
function state(step:string){
  const progress=job.value?.progress?.steps[step]
  if(job.value&&['completed','failed','cancelled','interrupted'].includes(job.value.status)&&progress&&active(progress))return job.value.status
  if(progress&&progress!=='pending')return progress
  if(job.value?.operation===step)return job.value.status
  if(step==='import'&&props.project.source||step==='transcribe'&&props.project.has_transcript||step==='analyze'&&props.project.has_analysis||step==='render'&&props.hasCuts)return 'completed'
  return 'pending'
}
</script>
<template>
  <aside class="pipeline-panel"><h2>Preparar seus cortes</h2><p>Preparação automática. Geração e revisão são suas.</p>
    <div v-for="([id,title],index) in names" :key="id" class="pipeline-step" :data-stage="id">
      <span class="step-mark" :class="{done:state(id)==='completed'}"><Check v-if="state(id)==='completed'" :size="16"/><span v-else>{{index+1}}</span></span>
      <div class="step-copy"><h3>{{title}}</h3><p>{{labels[state(id)]||state(id)}}</p>
        <div v-if="state(id)!=='pending'" role="progressbar" :aria-label="title" :aria-valuenow="state(id)==='completed'?100:undefined" aria-valuemin="0" aria-valuemax="100" class="stage-progress" :class="{indeterminate:['running','processing','cancelling'].includes(state(id)),complete:state(id)==='completed',failed:['failed','cancelled','interrupted'].includes(state(id))}"><span></span></div>
        <button v-if="id==='transcribe'&&!project.has_transcript&&!project.is_manual&&!processing" class="button small secondary" :disabled="busy||!project.source" @click="$emit('transcribe')">Transcrever vídeo</button>
        <button v-if="id==='analyze'&&!project.is_manual&&!processing&&project.has_transcript" class="button small secondary" :disabled="busy" @click="$emit('analyze')">{{project.has_analysis?'Nova análise':'Iniciar análise'}}</button>
        <button v-if="id==='render'&&!project.is_manual" class="button small secondary" :disabled="busy||processing||!project.has_analysis" @click="$emit('render')">Gerar prévias</button>
        <button v-if="id==='render'&&(hasCuts||project.is_manual)" class="button small primary" @click="$emit('review')">Revisar cortes</button>
      </div>
    </div>
    <div v-if="job" class="pipeline-activity" aria-live="polite"><p v-if="['analyze','prepare'].includes(job.operation)">{{job.requests_used||0}} de {{job.request_limit}} tentativas Gemini</p><p v-if="job.error" class="notice error">{{job.error.code}}: {{job.error.message}}</p><p v-if="job.exports?.length">{{job.exports.length}} pacote(s) exportado(s).</p><button v-if="processing" class="button small secondary" :disabled="job.status==='cancelling'" @click="$emit('cancel',job.id)"><Square :size="12"/>Cancelar</button><button v-else-if="['failed','cancelled','interrupted'].includes(job.status)&&!['prepare','analyze'].includes(job.operation)" class="button small secondary" @click="$emit('resume',job.id)"><RotateCcw :size="14"/>Retomar etapa</button><p v-else-if="['failed','cancelled','interrupted'].includes(job.status)&&job.operation==='prepare'">A sequência foi interrompida. Uma nova análise exige confirmar um novo limite de tentativas.</p></div>
    <p v-if="project.error&&!job?.error" class="notice error">{{project.error.code}}. Verifique a fonte e as configurações antes de tentar novamente.</p>
    <p class="pipeline-note">Mídia local. Gemini recebe somente texto. Barras animadas indicam atividade, sem percentual estimado.</p>
  </aside>
</template>
