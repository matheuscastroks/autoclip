<script setup lang="ts">
import AppButton from './AppButton.vue'
import {computed,ref,watch} from 'vue'
import {ArrowLeft,FolderOpen,FileText,Scissors,Play} from '@lucide/vue'
import type {Project,Transcript,Revision,Job,Decision,AnalysisView,AnalysisSelection} from '../types'
import {time,labels,active} from '../format'
import {notify} from '../notifications'
import ReviewPanel from './ReviewPanel.vue'
import PipelinePanel from './PipelinePanel.vue'
import AnalysisPanel from './AnalysisPanel.vue'
import GenerationQueue from './GenerationQueue.vue'
const props=defineProps<{project:Project;transcript:Transcript|null;revisions:Revision[];jobs:Job[];sourceUrl:string;previewUrl:string;busy:boolean;selectedRevision?:string;mediaLoading?:boolean;analysis?:AnalysisView|null;selection?:AnalysisSelection|null}>()
defineEmits<{back:[];folder:[];transcribe:[];analyze:[];render:[value:{analysis_hash:string;candidate_ids:string[]}];selection:[value:AnalysisSelection];cancel:[id:string];resume:[id:string];replaceSource:[id:string];select:[id:string];decision:[value:Decision];export:[];delete:[id:string];deleted:[]}>()
const tab=ref('overview'),player=ref<HTMLVideoElement>()
watch(()=>props.project.warnings,values=>{for(const warning of values)notify.warning(warning,{key:'project:'+props.project.id+':'+warning})},{immediate:true})
const processing=computed(()=>props.jobs.some(j=>active(j.status)))
const segments=computed(()=>props.transcript?.segments.length?props.transcript.segments:props.transcript?.words.reduce<{id:string;text:string;start_us:number;end_us:number}[]>((all,w,i)=>{if(i%12===0)all.push({id:w.id,text:w.text,start_us:w.start_us,end_us:w.end_us});else{all[all.length-1].text+=' '+w.text;all[all.length-1].end_us=w.end_us}return all},[])||[])
const tabs=['overview','transcript','analysis','cuts']
function tabKey(event:KeyboardEvent){const at=tabs.indexOf(tab.value);const next=event.key==='ArrowRight'?(at+1)%4:event.key==='ArrowLeft'?(at+3)%4:event.key==='Home'?0:event.key==='End'?3:-1;if(next<0)return;event.preventDefault();tab.value=tabs[next];(event.currentTarget as HTMLElement).querySelectorAll<HTMLButtonElement>('[role=tab]')[next]?.focus()}
function seek(us:number){if(player.value){player.value.currentTime=us/1e6;player.value.play().catch(()=>{})}}
</script>
<template>
  <AppButton class="back-link" @click="$emit('back')"><ArrowLeft :size="16"/>Todos os projetos</AppButton>
  <header class="page-heading project-heading"><div><h1>{{project.title||project.name}}</h1><div class="project-meta"><span>{{project.source?.channel||'Vídeo local'}}</span><span>{{project.duration_us?time(project.duration_us):'Duração pendente'}}</span><span class="status-pill" :data-status="project.status"><i></i>{{labels[project.status]||project.status}}</span></div></div><AppButton class="button secondary" @click="$emit('folder')"><FolderOpen :size="16"/>Abrir pasta</AppButton></header>
  <div class="project-tabs" role="tablist" aria-label="Áreas do projeto" @keydown="tabKey"><AppButton role="tab" id="tab-overview" aria-controls="project-panel" :tabindex="tab==='overview'?0:-1" :aria-selected="tab==='overview'" :class="{selected:tab==='overview'}" @click="tab='overview'"><Play :size="16"/>Visão geral</AppButton><AppButton role="tab" id="tab-transcript" aria-controls="project-panel" :tabindex="tab==='transcript'?0:-1" :aria-selected="tab==='transcript'" :class="{selected:tab==='transcript'}" @click="tab='transcript'"><FileText :size="16"/>Transcrição<span v-if="project.has_transcript">{{project.word_count.toLocaleString('pt-BR')}}</span></AppButton><AppButton role="tab" id="tab-analysis" aria-controls="project-panel" :tabindex="tab==='analysis'?0:-1" :aria-selected="tab==='analysis'" :class="{selected:tab==='analysis'}" @click="tab='analysis'"><FileText :size="16"/>Análise<span>{{analysis?.proposals.length||0}}</span></AppButton><AppButton role="tab" id="tab-cuts" aria-controls="project-panel" :tabindex="tab==='cuts'?0:-1" :aria-selected="tab==='cuts'" :class="{selected:tab==='cuts'}" @click="tab='cuts'"><Scissors :size="16"/>Cortes<span>{{revisions.length}}</span></AppButton></div>

  <div id="project-panel" role="tabpanel" :aria-labelledby="'tab-'+tab"><div v-if="tab==='overview'" class="workspace-overview">
    <PipelinePanel :source-url="sourceUrl" :selected-count="selection?.candidate_ids.length||0" :project="project" :jobs="jobs" :busy="busy" :has-cuts="revisions.length>0" :revisions="revisions" :analysis="analysis" @replace-source="$emit('replaceSource',$event)" @generate="selection?.analysis_hash&&$emit('render',{analysis_hash:selection.analysis_hash,candidate_ids:selection.candidate_ids})" @export="$emit('export')" @transcribe="$emit('transcribe')" @analyze="$emit('analyze')" @render="tab='analysis'" @analysis="tab='analysis'" @review="tab='cuts'" @cancel="$emit('cancel',$event)" @resume="$emit('resume',$event)"/>
  </div>
  <section v-else-if="tab==='transcript'" class="transcript-layout"><div class="transcript-header"><h2>Transcrição original</h2><p>{{project.word_count.toLocaleString('pt-BR')}} palavras · Português · Timestamps estimados pelo ASR</p></div><div v-if="transcript" class="transcript-body"><video v-if="sourceUrl" ref="player" :src="sourceUrl" controls preload="metadata"></video><div class="transcript-segments"><AppButton v-for="segment in segments" :key="segment.id" @click="seek(segment.start_us)"><time>{{time(segment.start_us)}}</time><span>{{segment.text}}</span></AppButton></div></div><div v-else class="empty-state"><FileText :size="32"/><h2>Ainda sem transcrição</h2><p>Inicie a etapa de transcrição na visão geral.</p></div></section>
  <AnalysisPanel v-else-if="tab==='analysis'" :analysis="analysis||null" :selection="selection||null" :jobs="jobs" :source-url="sourceUrl" :busy="busy||processing" @generate="$emit('render',$event)" @selection="$emit('selection',$event)"/>
  <section v-else><ReviewPanel :jobs="jobs" @resume="$emit('resume',$event)" :revisions="revisions" :manual="project.is_manual" :media-url="previewUrl" :selected-revision="selectedRevision" :media-loading="mediaLoading" :source-url="sourceUrl" :busy="busy" :processing="processing" @select="$emit('select',$event)" @decision="$emit('decision',$event)" @export="$emit('export')" @delete="$emit('delete',$event)" @deleted="$emit('deleted')"/></section></div>

</template>
