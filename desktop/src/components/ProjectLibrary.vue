<script setup lang="ts">
import AppButton from './AppButton.vue'
import AppSelect from './AppSelect.vue'
import {computed,ref} from 'vue'
import {Search,Film,Trash2,FolderOpen,Plus,FileVideo} from '@lucide/vue'
import type {Project} from '../types'
import {time,labels,stages} from '../format'
const props=defineProps<{projects:Project[];busy:boolean;covers?:Record<string,string>;activeProjects?:string[]}>()
defineEmits<{open:[id:string];create:[];import:[];delete:[id:string];trash:[]}>()
const query=ref(''),filter=ref('all')
const sort=ref('updated')
const stateOptions=computed(()=>[{value:'all',label:'Todos os projetos'},...Array.from(new Set(props.projects.map(p=>p.status))).map(state=>({value:state,label:labels[state]||state}))])
const brokenCovers=ref<Record<string,string>>({})
const filtered=computed(()=>props.projects.filter(p=>(p.title+' '+p.name).toLocaleLowerCase('pt-BR').includes(query.value.toLocaleLowerCase('pt-BR'))&&(filter.value==='all'||p.status===filter.value)).sort((a,b)=>sort.value==='name'?(a.title||a.name).localeCompare(b.title||b.name,'pt-BR'):b.updated_at-a.updated_at))
function updated(value:number){return value?new Date(value*1000).toLocaleString('pt-BR',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}):'—'}
</script>
<template>
  <header class="page-heading"><div><p class="breadcrumb">Biblioteca local</p><h1>Seus projetos<span class="heading-count">{{projects.length}}</span></h1><p>Do vídeo original ao trecho que vale compartilhar.</p></div><div class="actions"><AppButton class="button secondary" @click="$emit('import')" :disabled="busy||!!activeProjects?.length"><FolderOpen :size="17"/>Importar projeto</AppButton><AppButton class="button primary new-project-action" @click="$emit('create')" :disabled="busy||!!activeProjects?.length"><Plus :size="18"/>Novo projeto</AppButton></div></header>
  <section class="library-tools"><label class="search"><Search :size="17"/><input type="search" v-model="query" placeholder="Buscar projeto ou vídeo" aria-label="Buscar projetos"/></label><label class="filter">Estado<AppSelect v-model="filter" label="Filtrar por estado" :options="stateOptions"/></label><label class="filter">Ordenar<AppSelect v-model="sort" label="Ordenar projetos" :options="[{value:'updated',label:'Mais recentes'},{value:'name',label:'Nome do projeto'}]"/></label></section>
  <section class="project-table" aria-label="Projetos locais">
    <div class="table-head"><span>Projeto</span><span>Duração</span><span>Etapa / estado</span><span>Cortes</span><span>Atualizado</span><span>Ações</span></div>
    <div v-for="project in filtered"  :key="project.id" class="project-row" :data-project-id="project.id" @click="$emit('open',project.id)">
      <div class="project-name"><span class="video-thumb" :class="{manual:project.is_manual}"><img v-if="covers?.[project.id]&&brokenCovers[project.id]!==covers[project.id]" :src="covers[project.id]" alt="" loading="lazy" @error="brokenCovers[project.id]=covers?.[project.id]||''"/><Film v-else :size="26"/></span><div><AppButton class="project-title-link" @click.stop="$emit('open',project.id)"><strong>{{project.title||project.name}}</strong></AppButton><span>{{project.is_manual?'Teste de renderização':project.has_transcript?`${project.word_count.toLocaleString('pt-BR')} palavras transcritas`:project.name}}</span></div></div><span class="table-duration">{{project.duration_us?time(project.duration_us):'—'}}</span><span class="status-pill" :data-status="project.status"><i></i>{{project.summary?.stage?stages[project.summary.stage]||project.summary.stage:labels[project.status]||project.status}}</span><span class="project-counts"><span>{{project.summary?.proposed==null?'—':project.summary.proposed+' propostas'}}</span><small>{{project.summary?.selected==null?'—':project.summary.selected+' selecionados'}} · {{project.summary?.generated??'—'}} gerados</small></span><time class="project-updated" :title="project.updated_at?new Date(project.updated_at*1000).toLocaleString('pt-BR'):''">{{updated(project.updated_at)}}</time><AppButton type="button" class="icon-button" data-action="delete-project" title="Excluir projeto" :disabled="busy||activeProjects?.includes(project.id)" @click.stop="$emit('delete',project.id)"><Trash2 :size="16"/></AppButton>
    </div>
    <div v-if="!filtered.length" class="empty-state"><FileVideo :size="36"/><h2>{{projects.length?'Nenhum resultado':'Nenhum projeto ainda'}}</h2><p>{{projects.length?'Tente outro termo ou estado.':'Importe um vídeo ou abra uma pasta de projeto existente.'}}</p><AppButton v-if="!projects.length" class="button primary" @click="$emit('create')">Criar primeiro projeto</AppButton></div>
  </section>
  <AppButton class="button secondary" @click="$emit('trash')">Lixeira de projetos</AppButton><div class="library-foot"><span><span class="local-dot"></span>Mídia e transcrição ficam no seu computador</span><span>A seleção com IA envia somente texto, quando você iniciar.</span></div>
</template>
