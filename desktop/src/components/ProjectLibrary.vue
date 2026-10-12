<script setup lang="ts">
import {computed,ref} from 'vue'
import {Search,Film,ArrowUpRight,FolderOpen,Plus,FileVideo} from '@lucide/vue'
import type {Project} from '../types'
import {time,labels} from '../format'
const props=defineProps<{projects:Project[];busy:boolean}>()
defineEmits<{open:[id:string];create:[];import:[]}>()
const query=ref(''),filter=ref('all')
const filtered=computed(()=>props.projects.filter(p=>(p.title+' '+p.name).toLocaleLowerCase('pt-BR').includes(query.value.toLocaleLowerCase('pt-BR'))&&(filter.value==='all'||p.status===filter.value)))
</script>
<template>
  <header class="page-heading"><div><p class="breadcrumb">Biblioteca local</p><h1>Seus projetos<span class="heading-count">{{projects.length}}</span></h1><p>Do vídeo original ao trecho que vale compartilhar.</p></div><div class="actions"><button class="button secondary" @click="$emit('import')" :disabled="busy"><FolderOpen :size="17"/>Importar projeto</button><button class="button primary" @click="$emit('create')" :disabled="busy"><Plus :size="18"/>Novo projeto</button></div></header>
  <section class="library-tools"><label class="search"><Search :size="17"/><input type="search" v-model="query" placeholder="Buscar projeto ou vídeo" aria-label="Buscar projetos"/></label><label class="filter">Estado<select v-model="filter" aria-label="Filtrar por estado"><option value="all">Todos os projetos</option><option v-for="state in [...new Set(projects.map(p=>p.status))]" :key="state" :value="state">{{labels[state]||state}}</option></select></label></section>
  <section class="project-table" aria-label="Projetos locais">
    <div class="table-head"><span>Projeto</span><span>Duração</span><span>Estado</span><span></span></div>
    <button v-for="project in filtered" :key="project.id" class="project-row" :data-project-id="project.id" @click="$emit('open',project.id)">
      <div class="project-name"><span class="video-thumb" :class="{manual:project.is_manual}"><Film :size="26"/></span><div><strong>{{project.title||project.name}}</strong><span>{{project.is_manual?'Teste de renderização':project.has_transcript?`${project.word_count.toLocaleString('pt-BR')} palavras transcritas`:project.name}}</span></div></div><span class="table-duration">{{project.duration_us?time(project.duration_us):'—'}}</span><span class="status-pill" :data-status="project.status"><i></i>{{labels[project.status]||project.status}}</span><ArrowUpRight :size="18" class="row-arrow"/>
    </button>
    <div v-if="!filtered.length" class="empty-state"><FileVideo :size="36"/><h2>{{projects.length?'Nenhum resultado':'Nenhum projeto ainda'}}</h2><p>{{projects.length?'Tente outro termo ou estado.':'Importe um vídeo ou abra uma pasta de projeto existente.'}}</p><button v-if="!projects.length" class="button primary" @click="$emit('create')">Criar primeiro projeto</button></div>
  </section>
  <div class="library-foot"><span><span class="local-dot"></span>Mídia e transcrição ficam no seu computador</span><span>A seleção com IA envia somente texto, quando você iniciar.</span></div>
</template>
