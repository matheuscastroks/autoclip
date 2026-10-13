<script setup lang="ts">
import AppButton from './AppButton.vue'
import AppSelect from './AppSelect.vue'
import {computed,ref} from 'vue'
import {Search,Film,Trash2,Plus,FileVideo,ListOrdered,LayoutGrid,List,Clock,Sparkles} from '@lucide/vue'
import type {Project} from '../types'
import {time,labels,stages} from '../format'

const props=defineProps<{projects:Project[];busy:boolean;covers?:Record<string,string>;activeProjects?:string[]}>()
defineEmits<{open:[id:string];create:[];import:[];delete:[id:string];trash:[];queue:[]}>()

const query=ref('')
const filter=ref('all')
const sort=ref('updated')
const viewMode=ref<'grid'|'list'>('grid')
const brokenCovers=ref<Record<string,string>>({})

const stateOptions=computed(()=>[
  {value:'all',label:'Todos os estados'},
  ...Array.from(new Set(props.projects.map(p=>p.status))).map(state=>({value:state,label:labels[state]||state}))
])

const filtered=computed(()=>props.projects
  .filter(p=>(p.title+' '+p.name).toLocaleLowerCase('pt-BR').includes(query.value.toLocaleLowerCase('pt-BR'))&&(filter.value==='all'||p.status===filter.value))
  .sort((a,b)=>sort.value==='name'?(a.title||a.name).localeCompare(b.title||b.name,'pt-BR'):b.updated_at-a.updated_at)
)

function updated(value:number){
  return value?new Date(value*1000).toLocaleString('pt-BR',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}):'—'
}

function timeAgo(value:number){
  if(!value)return 'Recente'
  const diffSec=Math.floor(Date.now()/1000 - value)
  if(diffSec<60)return 'Agora mesmo'
  if(diffSec<3600)return `${Math.floor(diffSec/60)} min atrás`
  if(diffSec<86400)return `${Math.floor(diffSec/3600)} h atrás`
  return `${Math.floor(diffSec/86400)} d atrás`
}
</script>

<template>
  <div class="library-container">

    <!-- Banner Proeminente da Fila Global de Processamento -->
    <aside v-if="activeProjects?.length" class="global-queue-banner" @click="$emit('queue')">
      <div class="queue-banner-info">
        <span class="pulse-dot"></span>
        <div class="queue-banner-text">
          <strong>Processamento ativo em segundo plano</strong>
          <span>{{activeProjects.length}} projeto{{activeProjects.length===1?'':'s'}} executando na fila global local</span>
        </div>
      </div>
      <AppButton class="button small secondary queue-view-action" @click.stop="$emit('queue')">
        <ListOrdered :size="14"/>
        <span>Ver fila global</span>
      </AppButton>
    </aside>

    <!-- Barra de Ferramentas: Busca, Filtros, Ordenação e Alternador de Visão -->
    <section class="library-toolbar">
      <div class="search-box">
        <Search :size="16" class="search-icon"/>
        <input
          type="search"
          v-model="query"
          placeholder="Buscar projetos por título ou nome do arquivo…"
          aria-label="Buscar projetos"
        />
        <button v-if="query" type="button" class="clear-search" aria-label="Limpar busca" @click="query=''">✕</button>
      </div>

      <div class="toolbar-controls">
        <label class="control-label">
          <span>Estado:</span>
          <AppSelect v-model="filter" label="Filtrar por estado" :options="stateOptions"/>
        </label>

        <label class="control-label">
          <span>Ordenar:</span>
          <AppSelect v-model="sort" label="Ordenar projetos" :options="[{value:'updated',label:'Mais recentes'},{value:'name',label:'Nome do projeto'}]"/>
        </label>

        <div class="view-switcher" role="radiogroup" aria-label="Modo de visualização">
          <button
            type="button"
            class="view-btn"
            :class="{active:viewMode==='grid'}"
            role="radio"
            :aria-checked="viewMode==='grid'"
            :tabindex="viewMode==='grid'?0:-1"
            title="Visualização em Grade de Mídia"
            aria-label="Grade de Mídia"
            @click="viewMode='grid'"
            @keydown.right.prevent="viewMode='list'"
          >
            <LayoutGrid :size="16"/>
          </button>
          <button
            type="button"
            class="view-btn"
            :class="{active:viewMode==='list'}"
            role="radio"
            :aria-checked="viewMode==='list'"
            :tabindex="viewMode==='list'?0:-1"
            title="Visualização em Tabela Estruturada"
            aria-label="Tabela Estruturada"
            @click="viewMode='list'"
            @keydown.left.prevent="viewMode='grid'"
          >
            <List :size="16"/>
          </button>
        </div>
      </div>
    </section>

    <!-- ESTADO 1: GRADE VISUAL DE MÍDIA (Modo Padrão de Estúdio) -->
    <section v-if="filtered.length && viewMode==='grid'" class="projects-media-grid" aria-label="Projetos em grade">
      <article
        v-for="project in filtered"
        :key="project.id"
        class="media-project-card"
        :data-project-id="project.id"
        tabindex="0"
        role="button"
        :aria-label="'Abrir projeto: ' + (project.title || project.name)"
        @click="$emit('open',project.id)"
        @keydown.enter.prevent="$emit('open',project.id)"
        @keydown.space.prevent="$emit('open',project.id)"
      >
        <!-- Thumbnail 16:9 com Badges Flutuantes -->
        <div class="card-thumbnail-wrap">
          <img
            v-if="covers?.[project.id]&&brokenCovers[project.id]!==covers[project.id]"
            :src="covers[project.id]"
            alt=""
            loading="lazy"
            class="thumbnail-img"
            @error="brokenCovers[project.id]=covers?.[project.id]||''"
          />
          <div v-else class="thumbnail-fallback">
            <Film :size="32"/>
          </div>

          <!-- Duração do vídeo -->
          <span class="video-duration-tag">
            <Clock :size="11"/>
            {{project.duration_us?time(project.duration_us):'—'}}
          </span>

          <!-- Status do projeto -->
          <span class="status-pill card-status-pill" :data-status="project.status">
            <i></i>
            {{project.summary?.stage?stages[project.summary.stage]||project.summary.stage:labels[project.status]||project.status}}
          </span>
        </div>

        <!-- Conteúdo do Card -->
        <div class="card-body">
          <div class="card-header-row">
            <AppButton class="project-title-link" @click.stop="$emit('open',project.id)">
              <h2 class="project-card-title">{{project.title||project.name}}</h2>
            </AppButton>
          </div>

          <p class="project-source-info">
            {{project.is_manual?'Teste técnico de renderização':project.has_transcript?`${project.word_count.toLocaleString('pt-BR')} palavras transcritas`:project.name}}
          </p>

          <!-- Métricas de Cortes e IA -->
          <div class="project-metrics-row">
            <div class="metric-chip">
              <Sparkles :size="13"/>
              <span>{{project.summary?.proposed??'—'}} propostas</span>
            </div>
            <div class="metric-chip highlight" v-if="project.summary?.selected || project.summary?.generated">
              <span>{{project.summary?.selected??0}} selecionados · {{project.summary?.generated??0}} prontos</span>
            </div>
          </div>
        </div>

        <!-- Rodapé do Card com Ações Rápidas -->
        <div class="card-footer">
          <span class="updated-time" :title="project.updated_at?new Date(project.updated_at*1000).toLocaleString('pt-BR'):''">
            {{timeAgo(project.updated_at)}}
          </span>

          <div class="card-actions-group">
            <AppButton
              type="button"
              class="icon-button delete-btn"
              data-action="delete-project"
              title="Excluir projeto"
              :disabled="busy||activeProjects?.includes(project.id)"
              @click.stop="$emit('delete',project.id)"
            >
              <Trash2 :size="15"/>
            </AppButton>
            <span class="open-card-indicator">Abrir →</span>
          </div>
        </div>
      </article>
    </section>

    <!-- ESTADO 2: TABELA ESTRUTURADA (Modo Denso com todas as classes mantidas) -->
    <section v-else-if="filtered.length && viewMode==='list'" class="project-table" aria-label="Projetos locais">
      <div class="table-head">
        <span>Projeto</span>
        <span>Duração</span>
        <span>Etapa / estado</span>
        <span>Cortes</span>
        <span>Atualizado</span>
        <span>Ações</span>
      </div>
      <div
        v-for="project in filtered"
        :key="project.id"
        class="project-row"
        :data-project-id="project.id"
        tabindex="0"
        role="button"
        :aria-label="'Abrir projeto: ' + (project.title || project.name)"
        @click="$emit('open',project.id)"
        @keydown.enter.prevent="$emit('open',project.id)"
        @keydown.space.prevent="$emit('open',project.id)"
      >
        <div class="project-name">
          <span class="video-thumb" :class="{manual:project.is_manual}">
            <img
              v-if="covers?.[project.id]&&brokenCovers[project.id]!==covers[project.id]"
              :src="covers[project.id]"
              alt=""
              loading="lazy"
              @error="brokenCovers[project.id]=covers?.[project.id]||''"
            />
            <Film v-else :size="26"/>
          </span>
          <div>
            <AppButton class="project-title-link" @click.stop="$emit('open',project.id)">
              <strong>{{project.title||project.name}}</strong>
            </AppButton>
            <span>{{project.is_manual?'Teste de renderização':project.has_transcript?`${project.word_count.toLocaleString('pt-BR')} palavras transcritas`:project.name}}</span>
          </div>
        </div>

        <span class="table-duration">{{project.duration_us?time(project.duration_us):'—'}}</span>
        <span class="status-pill" :data-status="project.status">
          <i></i>{{project.summary?.stage?stages[project.summary.stage]||project.summary.stage:labels[project.status]||project.status}}
        </span>
        <span class="project-counts">
          <span>{{project.summary?.proposed==null?'—':project.summary.proposed+' propostas'}}</span>
          <small>{{project.summary?.selected==null?'—':project.summary.selected+' selecionados'}} · {{project.summary?.generated??'—'}} gerados</small>
        </span>
        <time class="project-updated" :title="project.updated_at?new Date(project.updated_at*1000).toLocaleString('pt-BR'):''">
          {{updated(project.updated_at)}}
        </time>
        <AppButton
          type="button"
          class="icon-button"
          data-action="delete-project"
          title="Excluir projeto"
          :disabled="busy||activeProjects?.includes(project.id)"
          @click.stop="$emit('delete',project.id)"
        >
          <Trash2 :size="16"/>
        </AppButton>
      </div>
    </section>

    <!-- ESTADO 3: ESTADO VAZIO / ONBOARDING INTEGRADO -->
    <section v-if="!filtered.length" class="empty-state studio-empty-state">
      <div class="empty-icon-wrap">
        <FileVideo :size="40"/>
      </div>
      <h2>{{projects.length?'Nenhum resultado encontrado':'Nenhum projeto ainda'}}</h2>
      <p>
        {{projects.length?'Tente outros termos de busca ou selecione outro filtro de estado.':'Comece importando um vídeo longo (entrevista, podcast, palestra) para gerar cortes verticais prontos para redes sociais.'}}
      </p>

      <div v-if="!projects.length" class="empty-quick-steps">
        <div class="step-mini-card">
          <span class="mini-step-num">1</span>
          <strong>Importe o vídeo</strong>
          <span>Cole a URL do YouTube ou selecione um arquivo local</span>
        </div>
        <div class="step-mini-card">
          <span class="mini-step-num">2</span>
          <strong>Transcrição & IA</strong>
          <span>O Whisper transcreve e o Gemini acha os melhores ganchos</span>
        </div>
        <div class="step-mini-card">
          <span class="mini-step-num">3</span>
          <strong>Cortes Verticais</strong>
          <span>Revise o vídeo 9:16 com legendas e baixe para postar</span>
        </div>
      </div>

      <AppButton v-if="!projects.length" class="button primary start-first-btn" @click="$emit('create')">
        <Plus :size="18"/>
        <span>Criar meu primeiro projeto</span>
      </AppButton>
    </section>

    <!-- Rodapé da Biblioteca -->
    <footer class="library-footer-bar">
      <AppButton class="button secondary small trash-access-btn" @click="$emit('trash')">
        <Trash2 :size="14"/>
        <span>Lixeira de projetos</span>
      </AppButton>

      <div class="library-privacy-guarantee">
        <span><span class="local-dot"></span>Privacidade Local-First: Mídia e transcrição ficam no seu computador</span>
        <span>A análise inteligente envia somente o texto transcrito</span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.library-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}


/* Banner de Fila */
.global-queue-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: var(--color-surface, #16191f);
  border: 1px solid var(--color-border-subtle, #2a303c);
  border-left: 4px solid var(--color-accent, #d97724);
  border-radius: 12px;
  padding: 12px 18px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.global-queue-banner:hover {
  background: var(--color-surface-raised, #1e232b);
  border-color: var(--color-accent, #d97724);
}
.queue-banner-info {
  display: flex;
  align-items: center;
  gap: 14px;
}
.queue-banner-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 0.84rem;
}
.queue-banner-text strong {
  color: var(--color-text-primary, #f2f4f7);
}
.queue-banner-text span {
  color: var(--color-text-muted, #9aa4b2);
}

/* Barra de Ferramentas */
.library-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  background: var(--color-surface, #16191f);
  border: 1px solid var(--color-border-subtle, #2a303c);
  border-radius: 12px;
  padding: 10px 14px;
}
.search-box {
  position: relative;
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 260px;
}
.search-icon {
  position: absolute;
  left: 12px;
  color: var(--color-text-muted, #9aa4b2);
  pointer-events: none;
}
.search-box input {
  width: 100%;
  min-height: 38px;
  padding: 8px 34px 8px 36px;
  background: var(--color-canvas, #0e1013);
  border: 1px solid var(--color-border-subtle, #2a303c);
  border-radius: 8px;
  color: var(--color-text-primary, #f2f4f7);
  font-size: 0.88rem;
  transition: border-color 0.15s ease;
}
.search-box input:focus {
  outline: none;
  border-color: var(--color-accent, #d97724);
}
.clear-search {
  position: absolute;
  right: 12px;
  color: var(--color-text-muted, #9aa4b2);
  cursor: pointer;
  font-size: 0.75rem;
}
.toolbar-controls {
  display: flex;
  align-items: center;
  gap: 14px;
}
.control-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.82rem;
  color: var(--color-text-muted, #9aa4b2);
}
.view-switcher {
  display: flex;
  align-items: center;
  background: var(--color-canvas, #0e1013);
  border: 1px solid var(--color-border-subtle, #2a303c);
  border-radius: 8px;
  padding: 2px;
  gap: 2px;
}
.view-btn {
  background: transparent;
  border: none;
  color: var(--color-text-muted, #9aa4b2);
  padding: 6px 8px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}
.view-btn.active {
  background: var(--color-surface-raised, #1e232b);
  color: var(--color-accent, #d97724);
}

/* GRADE DE MÍDIA */
.projects-media-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}
.media-project-card {
  background: var(--color-surface, #16191f);
  border: 1px solid var(--color-border-subtle, #2a303c);
  border-radius: 14px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  cursor: pointer;
  transition: all 0.2s ease;
}
.media-project-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-accent, #d97724);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.4);
}
.card-thumbnail-wrap {
  position: relative;
  aspect-ratio: 16/9;
  background: var(--color-canvas, #0e1013);
  overflow: hidden;
}
.thumbnail-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.thumbnail-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-muted, #9aa4b2);
}
.video-duration-tag {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(14, 16, 19, 0.85);
  backdrop-filter: blur(4px);
  color: var(--color-text-primary, #f2f4f7);
  font-size: 0.72rem;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-variant-numeric: tabular-nums;
}
.card-status-pill {
  position: absolute;
  top: 8px;
  left: 8px;
  backdrop-filter: blur(4px);
}
.card-body {
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}
.project-title-link {
  padding: 0;
  text-align: left;
  border: none;
  background: transparent;
  color: var(--color-text-primary, #f2f4f7);
}
.project-card-title {
  font-size: 0.98rem;
  font-weight: 600;
  line-height: 1.35;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.project-source-info {
  font-size: 0.78rem;
  color: var(--color-text-muted, #9aa4b2);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.project-metrics-row {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}
.metric-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: var(--color-surface-raised, #1e232b);
  border: 1px solid var(--color-border-subtle, #2a303c);
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.74rem;
  color: var(--color-text-muted, #9aa4b2);
}
.metric-chip.highlight {
  color: var(--color-accent, #d97724);
  border-color: rgba(217, 119, 36, 0.3);
}
.card-footer {
  padding: 10px 16px;
  border-top: 1px solid var(--color-border-subtle, #2a303c);
  background: rgba(14, 16, 19, 0.4);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.updated-time {
  font-size: 0.75rem;
  color: var(--color-text-muted, #9aa4b2);
}
.card-actions-group {
  display: flex;
  align-items: center;
  gap: 8px;
}
.open-card-indicator {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--color-accent, #d97724);
}

/* Estado Vazio */
.studio-empty-state {
  background: var(--color-surface, #16191f);
  border: 1px dashed var(--color-border-subtle, #2a303c);
  border-radius: 16px;
  padding: 48px 24px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}
.empty-icon-wrap {
  width: 72px;
  height: 72px;
  border-radius: 20px;
  background: var(--color-accent-soft, #2e1f12);
  color: var(--color-accent, #d97724);
  display: flex;
  align-items: center;
  justify-content: center;
}
.studio-empty-state h2 {
  font-size: 1.25rem;
  color: var(--color-text-primary, #f2f4f7);
  margin: 0;
}
.studio-empty-state p {
  color: var(--color-text-muted, #9aa4b2);
  max-width: 48ch;
  margin: 0;
}
.empty-quick-steps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  max-width: 720px;
  margin: 16px 0;
  text-align: left;
}
.step-mini-card {
  background: var(--color-surface-raised, #1e232b);
  border: 1px solid var(--color-border-subtle, #2a303c);
  border-radius: 10px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.mini-step-num {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--color-accent, #d97724);
}
.step-mini-card strong {
  font-size: 0.85rem;
  color: var(--color-text-primary, #f2f4f7);
}
.step-mini-card span {
  font-size: 0.75rem;
  color: var(--color-text-muted, #9aa4b2);
  line-height: 1.35;
}
.start-first-btn {
  font-weight: 600;
  padding: 10px 20px;
}

/* Rodapé */
.library-footer-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-top: 10px;
  border-top: 1px solid var(--color-border-subtle, #2a303c);
  flex-wrap: wrap;
}
.library-privacy-guarantee {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 0.75rem;
  color: var(--color-text-muted, #9aa4b2);
}

@media (max-width: 768px) {
  .empty-quick-steps {
    grid-template-columns: 1fr;
  }
}
</style>
