<script setup lang="ts">
import AppButton from './AppButton.vue'
import {computed,ref,watch} from 'vue'
import {Play,Search,Check,Scissors,FileText,RotateCcw,Sparkles,Clock,AlertTriangle,Volume2,Layers} from '@lucide/vue'
import type {AnalysisView,AnalysisSelection,Job,Proposal} from '../types'
import {time} from '../format'
import {notify} from '../notifications'
import AnalysisFeedback from './AnalysisFeedback.vue'

const props=defineProps<{analysis:AnalysisView|null;selection:AnalysisSelection|null;jobs:Job[];sourceUrl:string;busy:boolean}>()
const emit=defineEmits<{generate:[value:{analysis_hash:string;candidate_ids:string[]}];selection:[value:AnalysisSelection];resume:[]}>()
const topic=ref(''),search=ref(''),focused=ref(''),selected=ref<string[]>([]),player=ref<HTMLVideoElement>(),playEnd=ref(0)
const locallyEdited=ref(false)
const analysisLabels:Record<string,string>={not_started:'Análise ainda não iniciada',running:'Analisando a transcrição',partial:'Análise parcial disponível',completed:'Análise concluída',failed:'Análise precisa de atenção',cancelled:'Análise cancelada',interrupted:'Análise interrompida'}
const analysisStateLabel=computed(()=>analysisLabels[props.analysis?.state||'not_started']||'Estado da análise')
const complete=computed(()=>props.analysis?.state==='completed'&&!!props.analysis.analysis_hash)
const proposals=computed(()=>props.analysis?.proposals||[])
const filtered=computed(()=>proposals.value.filter(p=>(!topic.value||p.group_id===topic.value)&&(!search.value||[p.title,p.rationale,p.text].join(' ').toLocaleLowerCase('pt-BR').includes(search.value.toLocaleLowerCase('pt-BR')))))
const current=computed(()=>filtered.value.find(p=>p.candidate_id===focused.value)||filtered.value[0])

function overlapsWithSelected(p:Proposal):boolean{
  if(selected.value.includes(p.candidate_id))return false
  return validSelection.value.some(id=>{
    const other=proposals.value.find(cand=>cand.candidate_id===id)
    if(!other)return false
    return Math.min(p.end_us,other.end_us)>Math.max(p.start_us,other.start_us)
  })
}

const validSelection=computed(()=>{
  const result:string[]=[]
  for(const id of selected.value){
    const cand=proposals.value.find(p=>p.candidate_id===id&&p.eligible)
    if(!cand)continue
    const hasOverlap=result.some(keptId=>{
      const kept=proposals.value.find(p=>p.candidate_id===keptId)!
      return Math.min(cand.end_us,kept.end_us)>Math.max(cand.start_us,kept.start_us)
    })
    if(!hasOverlap)result.push(id)
  }
  return result
})

const totalSelectedDurationUs=computed(()=>{
  return validSelection.value.reduce((total,id)=>{
    const cand=proposals.value.find(p=>p.candidate_id===id)
    return total+(cand?.duration_us||0)
  },0)
})

const overlap=computed(()=>selected.value.length!==validSelection.value.length||validSelection.value.some((id,i)=>validSelection.value.slice(i+1).some(other=>{
  const a=proposals.value.find(p=>p.candidate_id===id)
  const b=proposals.value.find(p=>p.candidate_id===other)
  return !!(a&&b&&Math.min(a.end_us,b.end_us)>Math.max(a.start_us,b.start_us))
})))

const isPartial=computed(()=>{
  if(!props.analysis)return false
  return props.analysis.state!=='completed'&&props.analysis.state!=='running'&&props.analysis.completed_windows>0&&props.analysis.completed_windows<props.analysis.total_windows
})
const remainingWindows=computed(()=>Math.max(0,(props.analysis?.total_windows||0)-(props.analysis?.completed_windows||0)))

watch(()=>props.analysis?.analysis_hash,(hash,old)=>{if(hash!==old){locallyEdited.value=false;selected.value=hash&&props.selection?.analysis_hash===hash?[...props.selection.candidate_ids]:[];if(!proposals.value.some(p=>p.candidate_id===focused.value))focused.value='';if(!props.analysis?.topic_groups.some(g=>g.id===topic.value))topic.value=''}})
watch(()=>props.analysis?.job_id,(job,old)=>{if(old&&job!==old){focused.value='';topic.value='';selected.value=[];locallyEdited.value=false}})
watch(()=>props.selection,value=>{if(!locallyEdited.value&&value?.analysis_hash===props.analysis?.analysis_hash&&value?.analysis_hash)selected.value=[...value.candidate_ids]},{immediate:true})
watch(overlap,value=>{if(value)notify.warning('Seleção com trechos sobrepostos detectada. Os cortes não podem se sobrepor no vídeo original.')})
watch(current,value=>{if(value&&!value.eligible)notify.warning(value.reasons.join(' ')+' A geração permanece bloqueada.',{key:'proposal:'+value.candidate_id+':'+(props.analysis?.analysis_hash||props.analysis?.job_id)})})

function toggle(p:Proposal){
  if(!complete.value||!p.eligible||props.busy)return
  if(!selected.value.includes(p.candidate_id)&&overlapsWithSelected(p)){
    notify.warning('Este trecho se sobrepõe a outro corte já selecionado. Desmarque o corte concorrente primeiro.')
    return
  }
  locallyEdited.value=true
  selected.value=selected.value.includes(p.candidate_id)?selected.value.filter(id=>id!==p.candidate_id):[...selected.value,p.candidate_id]
  emit('selection',{schema_version:'1.0',analysis_hash:props.analysis!.analysis_hash,candidate_ids:[...validSelection.value]})
}

function play(context=false){if(!player.value||!current.value)return;player.value.currentTime=Math.max(0,current.value.start_us/1e6-(context?15:0));playEnd.value=(current.value.end_us/1e6)+(context?15:0);player.value.play().catch(()=>{})}
function stopAtEnd(){if(player.value&&playEnd.value&&player.value.currentTime>=playEnd.value){player.value.pause();playEnd.value=0}}
function choose(id:string){focused.value=id;player.value?.pause();playEnd.value=0}
</script>

<template>
  <section class="analysis-workspace">
    <!-- CABEÇALHO DO WORKSPACE DE CURADORIA -->
    <header class="analysis-heading">
      <div>
        <span class="eyebrow">Curadoria Editorial com Inteligência Artificial</span>
        <h2>Temas e propostas</h2>
        <p v-if="analysis">
          {{analysisStateLabel}}
          <span v-if="analysis.model"> · {{analysis.model}}</span>
          · {{analysis.completed_windows}}/{{analysis.total_windows}} janelas validadas
          · {{proposals.length}} propostas
          <span v-if="!complete"> · Resultado parcial</span>
        </p>
        <p v-else>A análise organizará os temas e os trechos da transcrição.</p>
      </div>

      <AppButton
        class="button primary generate-cta-btn"
        data-action="generate-selected"
        :disabled="!complete||!validSelection.length||busy||overlap"
        @click="emit('generate',{analysis_hash:analysis!.analysis_hash!,candidate_ids:[...validSelection]})"
      >
        <Scissors :size="16"/>Gerar {{validSelection.length}} prévia{{validSelection.length===1?'':'s'}}
      </AppButton>
    </header>

    <!-- BANNER DE RETOMADA COM 1 CLIQUE SE ANÁLISE FOR PARCIAL -->
    <div v-if="isPartial" class="analysis-resume-card" role="status">
      <div class="resume-info">
        <strong>Análise parcial · {{analysis?.completed_windows}} de {{analysis?.total_windows}} janelas validadas</strong>
        <p>Faltam {{remainingWindows}} janela{{remainingWindows===1?'':'s'}} para concluir a análise completa. Você já pode consultar as propostas validadas ou continuar o processamento agora.</p>
        <small v-if="analysis?.state==='failed'||analysis?.state==='interrupted'">Se a análise foi interrompida por limite de cota do Gemini (erro 429), aguarde alguns segundos antes de continuar.</small>
      </div>
      <AppButton class="button primary resume-analysis-btn" data-action="resume-analysis" :disabled="busy" @click="emit('resume')">
        <RotateCcw :size="16"/>Continuar análise das {{remainingWindows}} janelas restantes
      </AppButton>
    </div>

    <div v-else-if="!complete" class="subtle partial-notice-bar" role="status">
      As propostas já validadas podem ser consultadas. A geração fica disponível quando a análise completa terminar.
    </div>

    <!-- NOVO LAYOUT DESKTOP 2 COLUNAS: FILTROS & LISTA À ESQUERDA | SUITE DE INSPEÇÃO À DIREITA -->
    <div class="analysis-layout curation-2col-layout">
      
      <!-- COLUNA ESQUERDA (380px): SELETOR DE TEMAS + BUSCA + LISTA DE PROPOSTAS -->
      <aside class="curation-sidebar">
        <!-- Filtro de Temas (Chips Horizontais com Contadores) -->
        <div class="topic-list" role="tablist" aria-label="Temas identificados">
          <div class="topic-list-header">
            <span class="selection-step">01 · Escolha um tema</span>
            <h3>Temas identificados</h3>
          </div>
          <div class="topic-chips-scroll">
            <AppButton class="topic-chip-btn" :class="{selected:!topic}" @click="topic='';focused=''">
              Todos os temas <span>{{proposals.length}}</span>
            </AppButton>
            <AppButton
              v-for="group in analysis?.topic_groups"
              :key="group.id"
              class="topic-chip-btn"
              :class="{selected:topic===group.id}"
              @click="topic=group.id;focused=''"
            >
              {{group.label}}<span>{{proposals.filter(p=>p.group_id===group.id).length}}</span>
            </AppButton>
          </div>
          <div v-if="topic" class="topic-summary">
            <p v-for="summary in analysis?.topic_groups.find(g=>g.id===topic)?.summaries" :key="summary">{{summary}}</p>
          </div>
        </div>

        <!-- Lista de Propostas com Busca e Detecção de Conflitos -->
        <div class="proposal-column">
          <div class="proposal-column-header">
            <span class="selection-step">02 · Escolha um trecho</span>
            <span class="proposal-count-tag">{{filtered.length}} proposta(s)</span>
          </div>

          <label class="search">
            <Search :size="16"/>
            <input v-model="search" type="search" placeholder="Buscar nas propostas por palavra..." aria-label="Buscar nas propostas"/>
          </label>

          <div class="proposal-list hidden-scrollbar" tabindex="0" aria-label="Propostas de cortes">
            <article
              v-for="p in filtered"
              :key="p.candidate_id"
              class="proposal-card"
              :class="{selected:current?.candidate_id===p.candidate_id,overlapping:overlapsWithSelected(p)}"
            >
              <div class="proposal-top">
                <label class="proposal-checkbox" :title="overlapsWithSelected(p)?'Sobrepõe um corte já selecionado':undefined">
                  <input
                    type="checkbox"
                    :checked="selected.includes(p.candidate_id)"
                    :disabled="!complete||!p.eligible||busy||overlapsWithSelected(p)"
                    :aria-label="'Selecionar '+p.title"
                    @change="toggle(p)"
                  />
                </label>
                <AppButton class="proposal-open" @click="choose(p.candidate_id)">
                  <strong>{{p.title}}</strong>
                  <small>{{time(p.start_us)}} – {{time(p.end_us)}} · {{time(p.duration_us)}}</small>
                </AppButton>
              </div>

              <p class="proposal-summary">{{p.rationale}}</p>

              <div class="proposal-card-badges">
                <span v-if="overlapsWithSelected(p)" class="status-pill conflict-pill" data-status="warning" title="Este trecho se sobrepõe a outro corte já selecionado">
                  <AlertTriangle :size="12"/>Sobrepõe seleção
                </span>
                <span v-else class="status-pill" :data-status="p.eligible?'analyzed':'failed'">
                  <Check v-if="p.eligible" :size="12"/>{{p.eligible?'Elegível para prévia':'Precisa de atenção'}}
                </span>
              </div>
            </article>

            <p v-if="!filtered.length" class="subtle empty-proposals">
              {{proposals.length?'Nenhuma proposta corresponde ao filtro.':'Aguardando propostas validadas.'}}
            </p>
          </div>
        </div>
      </aside>

      <!-- COLUNA DIREITA: SUITE COMPLETA DE INSPEÇÃO DO CORTE SELECIONADO -->
      <main class="curation-inspection-main">
        <section v-if="current" class="proposal-detail">
          <div class="proposal-inspection">
            <div class="inspection-head">
              <span class="selection-step">03 · Confira e selecione</span>
              <div class="inspection-time-badge">
                <Clock :size="13"/>
                <span>{{time(current.start_us)}} – {{time(current.end_us)}} ({{time(current.duration_us)}})</span>
              </div>
            </div>

            <h3>{{current.title}}</h3>

            <!-- Mini Player de Audição Rápida -->
            <div class="inspection-media-box">
              <video v-if="sourceUrl" ref="player" :src="sourceUrl" controls preload="metadata" playsinline @timeupdate="stopAtEnd"></video>
              <div class="proposal-play">
                <AppButton class="button small primary" :disabled="!sourceUrl" @click="play()">
                  <Play :size="14"/>Ouvir trecho
                </AppButton>
                <AppButton class="button small secondary" :disabled="!sourceUrl" @click="play(true)">
                  Com contexto (+15s)
                </AppButton>
              </div>
            </div>

            <!-- Gancho Social em Destaque -->
            <details class="proposal-copy" open>
              <summary>Frase de abertura · 7 segundos</summary>
              <div class="opening-copy">
                <small>Frase de abertura · primeiros 7 segundos</small>
                <p>{{current.opening_text||'A próxima análise poderá sugerir uma frase curta para este trecho.'}}</p>
              </div>
            </details>

            <!-- Raciocínio Editorial e Por que Funciona -->
            <div class="inspection-block">
              <div class="block-title">
                <Sparkles :size="15"/>
                <strong>Por que este corte funciona</strong>
              </div>
              <p class="proposal-rationale">{{current.rationale}}</p>
            </div>

            <!-- Checklist Editorial -->
            <div class="editorial-flags">
              <span v-for="(label,key) in {completeness:'Raciocínio completo',standalone_context:'Contexto suficiente',qualification_preserved:'Ressalvas preservadas'}" :key="key">
                {{label}} <b>{{current.editorial[key]==='yes'?'Sim':current.editorial[key]==='no'?'Não':'Incerto'}}</b>
              </span>
            </div>

            <AppButton v-if="!current.eligible" class="text-button" @click="notify.warning(current.reasons.join(' ')+' A geração permanece bloqueada.')">
              Ver motivo da restrição
            </AppButton>
            <p v-for="warning in current.warnings" :key="warning" class="subtle">{{warning}}</p>

            <!-- Transcrição Completa e Contexto -->
            <details class="proposal-transcript">
              <summary><FileText :size="14"/>Fala e contexto</summary>
              <p class="context-text">{{current.context_before}}</p>
              <p class="core-text">{{current.text}}</p>
              <p class="context-text">{{current.context_after}}</p>
            </details>
            <small class="evidence-subtext">{{current.evidence_word_ids.length}} referência(s) à transcrição original · Timestamps estimados pelo ASR</small>
          </div>

          <!-- Ação Principal de Seleção para o Corte Focado -->
          <div class="inspection-footer-actions">
            <AppButton
              class="button primary select-focused-btn"
              data-action="select-focused"
              :disabled="!complete||!current.eligible||busy||(!selected.includes(current.candidate_id)&&overlapsWithSelected(current))"
              :title="!selected.includes(current.candidate_id)&&overlapsWithSelected(current)?'Sobrepõe um corte já selecionado':undefined"
              @click="toggle(current)"
            >
              <Check v-if="selected.includes(current.candidate_id)" :size="16"/>
              {{selected.includes(current.candidate_id)?'Remover da seleção':'Selecionar este trecho'}}
            </AppButton>
            
            <p v-if="!selected.includes(current.candidate_id)&&overlapsWithSelected(current)" class="subtle overlap-notice">
              Este trecho se sobrepõe a um corte já selecionado. Desmarque o corte concorrente para poder selecioná-lo.
            </p>
          </div>
        </section>

        <section v-else class="proposal-detail proposal-empty" aria-label="Inspeção do trecho">
          <FileText :size="36"/>
          <h3>{{proposals.length?'Escolha uma proposta':'Os trechos aparecerão aqui'}}</h3>
          <p>{{proposals.length?'Confira o conteúdo original, a justificativa e a integridade antes de selecionar.':'Quando houver propostas validadas, você poderá ouvir o contexto e escolher os cortes nesta área.'}}</p>
        </section>
      </main>
    </div>

    <!-- BARRA INFERIOR PERSISTENTE DE SELEÇÃO E AÇÃO -->
    <div class="curation-floating-bar" v-if="complete&&proposals.length>0">
      <div class="floating-selection-info">
        <span class="selection-count-pill">{{validSelection.length}}</span>
        <div>
          <strong>{{validSelection.length}} corte{{validSelection.length===1?'':'s'}} selecionado{{validSelection.length===1?'':'s'}}</strong>
          <small v-if="validSelection.length">Duração total estimada: ~{{time(totalSelectedDurationUs)}}</small>
          <small v-else>Selecione os melhores trechos para gerar vídeos 9:16 verticais</small>
        </div>
      </div>

      <AppButton
        class="button primary generate-floating-btn"
        data-action="generate-selected-floating"
        :disabled="!complete||!validSelection.length||busy||overlap"
        @click="emit('generate',{analysis_hash:analysis!.analysis_hash!,candidate_ids:[...validSelection]})"
      >
        <Scissors :size="16"/>Gerar {{validSelection.length}} prévia{{validSelection.length===1?'':'s'}} {{validSelection.length===1?'vertical':'verticais'}}
      </AppButton>
    </div>

    <details class="analysis-explanation">
      <summary>Resumo da análise em andamento</summary>
      <AnalysisFeedback :jobs="jobs"/>
    </details>
  </section>
</template>

<style scoped>
.analysis-workspace {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.curation-2col-layout {
  display: grid;
  grid-template-columns: 390px minmax(0, 1fr) !important;
  gap: 20px;
  align-items: start;
}

.curation-sidebar {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.topic-list {
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: var(--radius-panel, 14px);
  padding: 14px;
}

.topic-list-header {
  margin-bottom: 10px;
}

.topic-chips-scroll {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 180px;
  overflow-y: auto;
}

.topic-chip-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  text-align: left;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 0.8rem;
  background: transparent;
  border: 1px solid transparent;
  color: var(--color-text-secondary, var(--muted));
  transition: all 0.15s ease;
}

.topic-chip-btn:hover {
  background: var(--color-surface-hover, var(--soft));
  color: var(--color-text-primary, var(--ink));
}

.topic-chip-btn.selected {
  background: var(--color-accent-subtle, var(--accent-soft));
  border-color: var(--color-accent, #6366f1);
  color: var(--color-accent-text, var(--accent));
  font-weight: 600;
}

.topic-chip-btn span {
  font-size: 0.72rem;
  opacity: 0.8;
  background: var(--color-surface-raised, rgba(255,255,255,0.06));
  padding: 1px 6px;
  border-radius: 4px;
}

.proposal-column {
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: var(--radius-panel, 14px);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.proposal-column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.proposal-count-tag {
  font-size: 0.75rem;
  color: var(--color-text-muted, var(--muted));
}

.proposal-list {
  max-height: calc(var(--work-area-height, 480px) - 100px);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-right: 4px;
}

.proposal-card {
  background: var(--color-surface-raised, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: 10px;
  padding: 12px;
  transition: all 0.15s ease;
}

.proposal-card:hover {
  border-color: var(--color-border-strong, #555);
}

.proposal-card.selected {
  border-color: var(--color-accent, #6366f1);
  background: rgba(99, 102, 241, 0.05);
}

.proposal-card.overlapping {
  opacity: 0.8;
}

.proposal-top {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.proposal-checkbox {
  padding-top: 3px;
}

.proposal-checkbox input {
  width: 17px;
  height: 17px;
  accent-color: var(--color-accent, #6366f1);
  cursor: pointer;
}

.proposal-card-badges {
  display: flex;
  gap: 6px;
  margin-top: 8px;
}

.conflict-pill {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.12);
  border-color: rgba(245, 158, 11, 0.3);
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.curation-inspection-main {
  min-width: 0;
}

.proposal-detail {
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: var(--radius-panel, 14px);
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.inspection-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.inspection-time-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.77rem;
  color: var(--color-text-muted, var(--muted));
  background: var(--color-surface-hover, var(--soft));
  padding: 3px 8px;
  border-radius: 6px;
}

.proposal-detail h3 {
  font-size: 1.25rem;
  font-weight: 600;
  line-height: 1.3;
  margin: 0;
  color: var(--color-text-primary, var(--ink));
}

.inspection-media-box {
  background: #000;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--color-border-subtle, var(--line));
}

.inspection-media-box video {
  width: 100%;
  aspect-ratio: 16/9;
  max-height: 240px;
  display: block;
  object-fit: cover;
}

.inspection-block {
  background: var(--color-surface-hover, var(--soft));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: 10px;
  padding: 12px 16px;
}

.inspection-block .block-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--color-accent, #6366f1);
  margin-bottom: 6px;
}

.inspection-footer-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 14px;
  border-top: 1px solid var(--color-border-subtle, var(--line));
}

.select-focused-btn {
  min-height: 40px;
  font-size: 0.9rem;
  font-weight: 600;
}

.curation-floating-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-accent, rgba(99, 102, 241, 0.4));
  border-radius: 14px;
  padding: 14px 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
}

.floating-selection-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.selection-count-pill {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-accent, #6366f1);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.9rem;
}

.floating-selection-info strong {
  font-size: 0.92rem;
  display: block;
}

.floating-selection-info small {
  font-size: 0.77rem;
  color: var(--color-text-muted, var(--muted));
}

.generate-floating-btn {
  font-size: 0.9rem;
  font-weight: 600;
  padding: 10px 20px;
}

.analysis-resume-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-left: 4px solid var(--color-accent, var(--accent));
  border-radius: 10px;
  padding: 14px 18px;
}

.resume-info strong {
  display: block;
  font-size: 0.95rem;
  margin-bottom: 4px;
}

.resume-info p {
  margin: 0 0 4px;
  font-size: 0.85rem;
  color: var(--color-text-muted, var(--muted));
}

.resume-info small {
  display: block;
  font-size: 0.78rem;
  color: var(--color-warning-text, #f59e0b);
}

.resume-analysis-btn {
  white-space: nowrap;
  flex-shrink: 0;
}

.overlap-notice {
  margin-top: 6px;
  color: var(--color-warning-text, #f59e0b);
  font-size: 0.82rem;
  font-weight: 500;
}

@media (max-width: 900px) {
  .curation-2col-layout {
    grid-template-columns: 1fr !important;
  }
}
</style>
