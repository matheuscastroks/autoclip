<script setup lang="ts">
import {computed,ref} from 'vue'
import {ArrowLeft,FolderOpen,FileText,Scissors,Play,Check,AlertCircle,ChevronRight} from '@lucide/vue'
import type {Project,Transcript,Revision,Job,Decision} from '../types'
import {time,labels,active} from '../format'
import ReviewPanel from './ReviewPanel.vue'
import PipelinePanel from './PipelinePanel.vue'
const props=defineProps<{project:Project;transcript:Transcript|null;revisions:Revision[];jobs:Job[];sourceUrl:string;previewUrl:string;busy:boolean;selectedRevision?:string;mediaLoading?:boolean}>()
defineEmits<{back:[];folder:[];transcribe:[];analyze:[];render:[];cancel:[id:string];resume:[id:string];select:[id:string];decision:[value:Decision];export:[];delete:[id:string];deleted:[]}>()
const tab=ref('overview'),player=ref<HTMLVideoElement>()
const processing=computed(()=>props.jobs.some(j=>active(j.status)))
const segments=computed(()=>props.transcript?.segments.length?props.transcript.segments:props.transcript?.words.reduce<{id:string;text:string;start_us:number;end_us:number}[]>((all,w,i)=>{if(i%12===0)all.push({id:w.id,text:w.text,start_us:w.start_us,end_us:w.end_us});else{all[all.length-1].text+=' '+w.text;all[all.length-1].end_us=w.end_us}return all},[])||[])
function seek(us:number){if(player.value){player.value.currentTime=us/1e6;player.value.play().catch(()=>{})}}
</script>
<template>
  <button class="back-link" @click="$emit('back')"><ArrowLeft :size="16"/>Todos os projetos</button>
  <header class="page-heading project-heading"><div><h1>{{project.title||project.name}}</h1><div class="project-meta"><span>{{project.source?.channel||'Vídeo local'}}</span><span>{{project.duration_us?time(project.duration_us):'Duração pendente'}}</span><span class="status-pill" :data-status="project.status"><i></i>{{labels[project.status]||project.status}}</span></div></div><button class="button secondary" @click="$emit('folder')"><FolderOpen :size="16"/>Abrir pasta</button></header>
  <div class="project-tabs" role="tablist" aria-label="Áreas do projeto"><button role="tab" :aria-selected="tab==='overview'" :class="{selected:tab==='overview'}" @click="tab='overview'"><Play :size="16"/>Visão geral</button><button role="tab" :aria-selected="tab==='transcript'" :class="{selected:tab==='transcript'}" @click="tab='transcript'"><FileText :size="16"/>Transcrição<span v-if="project.has_transcript">{{project.word_count.toLocaleString('pt-BR')}}</span></button><button role="tab" :aria-selected="tab==='cuts'" :class="{selected:tab==='cuts'}" @click="tab='cuts'"><Scissors :size="16"/>Cortes<span>{{revisions.length}}</span></button></div>
  <div v-for="warning in project.warnings" :key="warning" class="notice"><AlertCircle :size="17"/>{{warning}}</div>
  <div v-if="tab==='overview'" class="workspace-overview">
    <div class="original-column"><div class="video-surface"><video v-if="sourceUrl" ref="player" :src="sourceUrl" controls preload="metadata" playsinline></video><div v-else class="video-unavailable">{{project.source?'Vídeo indisponível':'Importação em andamento'}}</div><span class="original-tag">Original</span></div><div class="source-info"><FileText :size="17"/><div><strong>Fonte preservada</strong><p>{{project.source?.attribution||'Os metadados aparecerão após a importação.'}}</p></div></div></div>
    <PipelinePanel :project="project" :jobs="jobs" :busy="busy" :has-cuts="revisions.length>0" @transcribe="$emit('transcribe')" @analyze="$emit('analyze')" @render="$emit('render')" @review="tab='cuts'" @cancel="$emit('cancel',$event)" @resume="$emit('resume',$event)"/>
  </div>
  <section v-else-if="tab==='transcript'" class="transcript-layout"><div class="transcript-header"><h2>Transcrição original</h2><p>{{project.word_count.toLocaleString('pt-BR')}} palavras · Português · Timestamps estimados pelo ASR</p></div><div v-if="transcript" class="transcript-body"><video v-if="sourceUrl" ref="player" :src="sourceUrl" controls preload="metadata"></video><div class="transcript-segments"><button v-for="segment in segments" :key="segment.id" @click="seek(segment.start_us)"><time>{{time(segment.start_us)}}</time><span>{{segment.text}}</span></button></div></div><div v-else class="empty-state"><FileText :size="32"/><h2>Ainda sem transcrição</h2><p>Inicie a etapa de transcrição na visão geral.</p></div></section>
  <ReviewPanel v-else :revisions="revisions" :manual="project.is_manual" :media-url="previewUrl" :selected-revision="selectedRevision" :media-loading="mediaLoading" :source-url="sourceUrl" :busy="busy||processing" @select="$emit('select',$event)" @decision="$emit('decision',$event)" @export="$emit('export')" @delete="$emit('delete',$event)" @deleted="$emit('deleted')"/>

</template>
