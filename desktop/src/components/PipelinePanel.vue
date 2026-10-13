<script setup lang="ts">
import AppButton from './AppButton.vue'
import {computed,watch} from 'vue'
import {Check,Square,RotateCcw} from '@lucide/vue'
import type {Project,Job,Revision,AnalysisView} from '../types'
import {active,labels,latestJob} from '../format'
import {notifyJob,notify} from '../notifications'
const props=defineProps<{project:Project;jobs:Job[];busy:boolean;hasCuts:boolean;revisions?:Revision[];analysis?:AnalysisView|null;sourceUrl?:string;selectedCount?:number}>()
defineEmits<{transcribe:[];analyze:[];render:[];analysis:[];review:[];cancel:[id:string];resume:[id:string];replaceSource:[id:string];generate:[];export:[]}>()
const names=[['import','Importar vídeo'],['transcribe','Transcrever'],['analyze','Analisar temas'],['choose','Escolher trechos'],['render','Gerar prévias'],['export','Exportar']] as const
const groups=[{title:'Preparação automática',description:'O motor importa, transcreve e identifica os temas.',steps:names.slice(0,3)},{title:'Seleção e entrega',description:'Escolha os trechos, gere os vídeos e baixe para publicar.',steps:names.slice(3)}]
const job=computed(()=>latestJob(props.jobs))
const recovery=computed(()=>job.value&&['failed','cancelled','interrupted'].includes(job.value.status))
const importRecovery=computed(()=>recovery.value&&!props.project.source&&['prepare','import'].includes(job.value?.operation||''))
const approved=computed(()=>props.revisions?.some(r=>r.technical_pass))
watch(job,value=>{if(value&&['failed','interrupted'].includes(value.status))notifyJob(value)},{immediate:true})
const processing=computed(()=>props.jobs.some(j=>active(j.status)))
function state(step:string){
  if(step==='choose')return props.selectedCount?'completed':props.project.has_analysis?'waiting':'pending'
  if(step==='export'&&props.revisions?.some(r=>r.exported))return 'completed'
  if(step==='import'&&importRecovery.value)return job.value!.status
  const progress=job.value?.progress?.steps[step]
  if(job.value&&['completed','failed','cancelled','interrupted'].includes(job.value.status)&&progress&&['running','cancelling'].includes(progress))return job.value.status
  if(progress&&progress!=='pending')return progress
  if(job.value?.operation===step)return job.value.status
  if(step==='import'&&props.project.source||step==='transcribe'&&props.project.has_transcript||step==='analyze'&&props.project.has_analysis||step==='render'&&props.hasCuts)return 'completed'
  return 'pending'
}
</script>
<template>
  <section class="pipeline-panel" aria-label="Preparar seus cortes">
    <header class="preparation-header">
      <div class="preparation-intro"><span class="section-eyebrow">Fluxo do projeto</span><div class="pipeline-title"><h2>Preparar seus cortes</h2><AppButton v-if="processing&&job" class="button small secondary" :disabled="job.status==='cancelling'" @click="$emit('cancel',job.id)"><Square :size="12"/>Cancelar</AppButton></div><p>Avance por etapas e acompanhe cada entrega.</p><p class="preparation-summary">{{project.has_transcript?project.word_count.toLocaleString('pt-BR')+' palavras transcritas':'Transcrição pendente'}} · {{analysis?.topic_groups.length||0}} temas · {{revisions?.length||0}} prévias</p></div>
      <figure class="pipeline-video"><video v-if="sourceUrl" :src="sourceUrl" controls preload="metadata" playsinline aria-label="Vídeo original em miniatura"></video><div v-else class="pipeline-video-empty">{{project.source?'Vídeo indisponível':importRecovery?'Importação interrompida':processing&&job?.progress?.steps.import==='running'?'Importando vídeo…':'Vídeo ainda não importado'}}</div><figcaption>Vídeo original · {{project.source?'Fonte preservada':'Aguardando fonte'}}</figcaption></figure>
    </header>

    <div class="preparation-groups"><section v-for="group in groups" :key="group.title" class="preparation-group"><header><h3>{{group.title}}</h3><p>{{group.description}}</p></header>
      <ol class="pipeline-steps"><li v-for="[id,title] in group.steps" :key="id" class="pipeline-step" :data-stage="id" :data-state="state(id)">
        <span class="step-mark" :class="{done:state(id)==='completed'}"><Check v-if="state(id)==='completed'" :size="16"/><span v-else>{{names.findIndex(n=>n[0]===id)+1}}</span></span>
        <div class="step-copy"><div class="step-heading"><h3>{{title}}</h3><p>{{state(id)==='waiting'?'Sua próxima ação':labels[state(id)]||state(id)}}</p></div>
          <div v-if="!['pending','waiting'].includes(state(id))" role="progressbar" :aria-label="title" :aria-valuenow="state(id)==='completed'?100:undefined" aria-valuemin="0" aria-valuemax="100" class="stage-progress" :class="{indeterminate:['running','processing','cancelling'].includes(state(id)),complete:state(id)==='completed',failed:['failed','cancelled','interrupted'].includes(state(id))}"><span></span></div>
          <div v-if="id==='import'&&importRecovery&&job" class="import-recovery"><p>Importação interrompida. Escolha como continuar.</p><AppButton v-if="job.error" type="button" class="text-button" data-action="error-details" @click="notifyJob(job,true)">Ver motivo da falha</AppButton><div class="step-actions"><AppButton class="button small primary" data-action="retry-import" :disabled="busy||processing" @click="$emit('resume',job.id)"><RotateCcw :size="14"/>Tentar novamente</AppButton><AppButton class="button small secondary" data-action="replace-source" :disabled="busy||processing" @click="$emit('replaceSource',job.id)">Usar arquivo local</AppButton></div></div>
          <AppButton v-if="id==='transcribe'&&!project.has_transcript&&!project.is_manual&&!processing" class="button small secondary" :disabled="busy||!project.source" @click="$emit('transcribe')">Transcrever vídeo</AppButton>
          <AppButton v-if="id==='analyze'&&!project.is_manual&&!processing&&project.has_transcript" class="button small secondary" :disabled="busy" @click="$emit('analyze')">{{project.has_analysis?'Nova análise':recovery?'Continuar análise':'Iniciar análise'}}</AppButton>
          <AppButton v-if="id==='choose'&&!project.is_manual" class="button small secondary" :disabled="busy||!project.has_analysis" @click="$emit('render')">{{selectedCount?selectedCount+' trechos selecionados · Ajustar':'Escolher trechos'}}</AppButton>
          <AppButton v-if="id==='render'&&!project.is_manual" class="button small primary" :disabled="busy||!selectedCount||!project.has_analysis" @click="$emit('generate')">Gerar prévias</AppButton>
          <AppButton v-if="id==='export'&&approved" class="button small primary" :disabled="busy" @click="$emit('export')">Exportar prontos</AppButton>
        </div>
      </li></ol></section></div>
    <div class="analysis-overview" v-if="project.has_transcript"><div><strong>{{analysis?.state==='completed'?'Análise concluída':analysis?.proposals.length?'Análise parcial disponível':'Acompanhe a análise'}}</strong><p v-if="analysis">{{analysis.completed_windows}}/{{analysis.total_windows}} janelas · {{analysis.topic_groups.length}} temas · {{analysis.proposals.length}} propostas</p></div><AppButton class="button small secondary" @click="$emit('analysis')">Ver análise</AppButton></div>
    <div v-if="job&&!importRecovery" class="pipeline-activity" aria-live="polite"><p v-if="['analyze','prepare'].includes(job.operation)&&project.has_transcript">{{job.requests_used||0}} chamada(s) Gemini{{job.request_mode==='automatic'?' · planejamento automático':' de '+job.request_limit}}</p><AppButton v-if="job.error" type="button" class="text-button" @click="notifyJob(job,true)">Ver motivo da falha</AppButton><p v-if="job.exports?.length">{{job.exports.length}} pacote(s) exportado(s).</p><AppButton v-if="recovery&&!['analyze','render'].includes(job.operation)" class="button small secondary" :disabled="busy||processing" @click="$emit('resume',job.id)"><RotateCcw :size="14"/>Continuar preparação</AppButton></div>
    <AppButton v-if="project.error&&!job" type="button" class="text-button" @click="notify.error(project.error.message)">Ver motivo da falha</AppButton>
    <footer class="pipeline-note">Preparação automática até a análise. Geração e download sob seu controle.</footer>
  </section>
</template>