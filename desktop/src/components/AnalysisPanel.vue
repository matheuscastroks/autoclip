<script setup lang="ts">
import AppButton from './AppButton.vue'
import {computed,ref,watch} from 'vue'
import {Play,Search,Check,Scissors,FileText,RotateCcw} from '@lucide/vue'
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
  <header class="analysis-heading"><div><span class="eyebrow">Conteúdo antes do formato</span><h2>Temas e propostas</h2><p v-if="analysis">{{analysisStateLabel}}<span v-if="analysis.model"> · {{analysis.model}}</span> · {{analysis.completed_windows}}/{{analysis.total_windows}} janelas validadas · {{proposals.length}} propostas<span v-if="!complete"> · Resultado parcial</span></p><p v-else>A análise organizará os temas e os trechos da transcrição.</p></div><AppButton class="button primary" data-action="generate-selected" :disabled="!complete||!validSelection.length||busy||overlap" @click="emit('generate',{analysis_hash:analysis!.analysis_hash!,candidate_ids:[...validSelection]})"><Scissors :size="16"/>Gerar {{validSelection.length}} prévia{{validSelection.length===1?'':'s'}}</AppButton></header>

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

  <div v-else-if="!complete" class="subtle" role="status">As propostas já validadas podem ser consultadas. A geração fica disponível quando a análise completa terminar.</div>

  <div class="analysis-layout">
   <aside class="topic-list"><span class="selection-step">01 · Escolha um tema</span><h3>Temas identificados</h3><AppButton :class="{selected:!topic}" @click="topic='';focused=''">Todos os temas <span>{{proposals.length}}</span></AppButton><AppButton v-for="group in analysis?.topic_groups" :key="group.id" :class="{selected:topic===group.id}" @click="topic=group.id;focused=''">{{group.label}}<span>{{proposals.filter(p=>p.group_id===group.id).length}}</span></AppButton><div v-if="topic" class="topic-summary"><p v-for="summary in analysis?.topic_groups.find(g=>g.id===topic)?.summaries" :key="summary">{{summary}}</p></div></aside>
   <div class="proposal-column"><span class="selection-step">02 · Escolha um trecho</span><label class="search"><Search :size="16"/><input v-model="search" type="search" placeholder="Buscar nas propostas" aria-label="Buscar nas propostas"/></label><div class="proposal-list hidden-scrollbar" tabindex="0" aria-label="Propostas de cortes"><article v-for="p in filtered" :key="p.candidate_id" class="proposal-card" :class="{selected:current?.candidate_id===p.candidate_id}"><div class="proposal-top"><label class="proposal-checkbox" :title="overlapsWithSelected(p)?'Sobrepõe um corte já selecionado':undefined"><input type="checkbox" :checked="selected.includes(p.candidate_id)" :disabled="!complete||!p.eligible||busy||overlapsWithSelected(p)" :aria-label="'Selecionar '+p.title" @change="toggle(p)"/></label><AppButton class="proposal-open" @click="choose(p.candidate_id)"><strong>{{p.title}}</strong><small>{{time(p.start_us)}} – {{time(p.end_us)}} · {{time(p.duration_us)}}</small></AppButton></div><p class="proposal-summary">{{p.rationale}}</p><span v-if="overlapsWithSelected(p)" class="status-pill" data-status="warning" title="Este trecho se sobrepõe a outro corte já selecionado">Sobrepõe seleção</span><span v-else class="status-pill" :data-status="p.eligible?'analyzed':'failed'"><Check v-if="p.eligible" :size="12"/>{{p.eligible?'Elegível para prévia':'Precisa de atenção'}}</span></article><p v-if="!filtered.length" class="subtle empty-proposals">{{proposals.length?'Nenhuma proposta corresponde ao filtro.':'Aguardando propostas validadas.'}}</p></div></div>
   <section v-if="current" class="proposal-detail"><div class="proposal-inspection"><span class="selection-step">03 · Confira e selecione</span><h3>{{current.title}}</h3><video v-if="sourceUrl" ref="player" :src="sourceUrl" controls preload="metadata" playsinline @timeupdate="stopAtEnd"></video><div class="proposal-play"><AppButton class="button small primary" :disabled="!sourceUrl" @click="play()"><Play :size="14"/>Ouvir trecho</AppButton><AppButton class="button small secondary" :disabled="!sourceUrl" @click="play(true)">Com contexto</AppButton></div><details class="proposal-copy"><summary>Frase de abertura · 7 segundos</summary><div class="opening-copy"><small>Frase de abertura · primeiros 7 segundos</small><p>{{current.opening_text||'A próxima análise poderá sugerir uma frase curta para este trecho.'}}</p></div></details><p class="proposal-rationale">{{current.rationale}}</p><div class="editorial-flags"><span v-for="(label,key) in {completeness:'Raciocínio completo',standalone_context:'Contexto suficiente',qualification_preserved:'Ressalvas preservadas'}" :key="key">{{label}} <b>{{current.editorial[key]==='yes'?'Sim':current.editorial[key]==='no'?'Não':'Incerto'}}</b></span></div><AppButton v-if="!current.eligible" class="text-button" @click="notify.warning(current.reasons.join(' ')+' A geração permanece bloqueada.')">Ver motivo da restrição</AppButton><p v-for="warning in current.warnings" :key="warning" class="subtle">{{warning}}</p><details class="proposal-transcript"><summary><FileText :size="14"/>Fala e contexto</summary><p class="context-text">{{current.context_before}}</p><p>{{current.text}}</p><p class="context-text">{{current.context_after}}</p></details><small>{{current.evidence_word_ids.length}} referência(s) à transcrição original · Timestamps estimados pelo ASR</small></div><AppButton class="button small primary" data-action="select-focused" :disabled="!complete||!current.eligible||busy||(!selected.includes(current.candidate_id)&&overlapsWithSelected(current))" :title="!selected.includes(current.candidate_id)&&overlapsWithSelected(current)?'Sobrepõe um corte já selecionado':undefined" @click="toggle(current)">{{selected.includes(current.candidate_id)?'Remover da seleção':'Selecionar este trecho'}}</AppButton><p v-if="!selected.includes(current.candidate_id)&&overlapsWithSelected(current)" class="subtle overlap-notice">Este trecho se sobrepõe a um corte já selecionado. Desmarque o corte concorrente para poder selecioná-lo.</p></section>
   <section v-else class="proposal-detail proposal-empty" aria-label="Inspeção do trecho"><FileText :size="28"/><h3>{{proposals.length?'Escolha uma proposta':'Os trechos aparecerão aqui'}}</h3><p>{{proposals.length?'Confira o conteúdo original, a justificativa e a integridade antes de selecionar.':'Quando houver propostas validadas, você poderá ouvir o contexto e escolher os cortes nesta área.'}}</p></section>
  </div>
  <details class="analysis-explanation"><summary>Resumo da análise em andamento</summary><AnalysisFeedback :jobs="jobs"/></details>
 </section>
</template>
<style scoped>
.analysis-resume-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  background: var(--surface-card, #ffffff);
  border: 1px solid var(--border-subtle, #e2e8f0);
  border-left: 4px solid var(--accent, #6d28d9);
  border-radius: 10px;
  padding: 14px 18px;
  margin-bottom: 16px;
}
.resume-info strong {
  display: block;
  font-size: 0.95rem;
  color: var(--text-main, #1e293b);
  margin-bottom: 4px;
}
.resume-info p {
  margin: 0 0 4px;
  font-size: 0.85rem;
  color: var(--text-muted, #64748b);
}
.resume-info small {
  display: block;
  font-size: 0.78rem;
  color: var(--amber-600, #d97706);
}
.resume-analysis-btn {
  white-space: nowrap;
  flex-shrink: 0;
}
.overlap-notice {
  margin-top: 8px;
  color: var(--amber-600, #d97706);
  font-size: 0.82rem;
}
</style>
