<script setup lang="ts">
import AppButton from './AppButton.vue'
import {computed,watch} from 'vue'
import {Check,Square,RotateCcw,LoaderCircle,AlertCircle,ArrowRight,Play,FileText,Sparkles,Scissors,Download,Film,Clock} from '@lucide/vue'
import type {Project,Job,Revision,AnalysisView} from '../types'
import {active,labels,latestJob,time} from '../format'
import {notifyJob,notify} from '../notifications'

const props=defineProps<{project:Project;jobs:Job[];busy:boolean;hasCuts:boolean;revisions?:Revision[];analysis?:AnalysisView|null;sourceUrl?:string;selectedCount?:number}>()
const emit=defineEmits<{transcribe:[];analyze:[];render:[];analysis:[];review:[];cancel:[id:string];resume:[id:string];replaceSource:[id:string];generate:[];export:[]}>()
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

function handleStepClick(id:string){
  if(id==='transcribe'&&props.project.has_transcript)emit('review')
  else if((id==='analyze'||id==='choose')&&props.project.has_analysis)emit('analysis')
  else if((id==='render'||id==='export')&&props.hasCuts)emit('review')
}

// Determinar recomendação contextual inteligente para o Hero
const activeAction=computed(()=>{
  if(importRecovery.value) return 'import-failed'
  if(!props.project.source) return 'importing'
  if(!props.project.has_transcript) return 'transcribe'
  if(!props.project.has_analysis) return 'analyze'
  if(!props.hasCuts && (!props.selectedCount || props.selectedCount === 0)) return 'choose'
  if(!props.hasCuts && props.selectedCount && props.selectedCount > 0) return 'render'
  if(props.hasCuts) return 'review'
  return 'idle'
})
</script>

<template>
  <section class="pipeline-panel" aria-label="Preparar seus cortes">
    <!-- CABEÇALHO DO PROJETO COM STATUS E CONTROLE DE CANCELAMENTO -->
    <header class="preparation-header">
      <div class="preparation-intro">
        <span class="section-eyebrow">Fluxo de Trabalho</span>
        <div class="pipeline-title">
          <h2>Preparar seus cortes</h2>
          <AppButton v-if="processing&&job" class="button small secondary cancel-job-btn" :disabled="job.status==='cancelling'" @click="$emit('cancel',job.id)">
            <Square :size="12"/>Cancelar
          </AppButton>
        </div>
        <p>Acompanhe a esteira de processamento e tome as decisões editoriais.</p>
        <p class="preparation-summary">{{project.has_transcript?project.word_count.toLocaleString('pt-BR')+' palavras transcritas':'Transcrição pendente'}} · {{analysis?.topic_groups.length||0}} temas · {{revisions?.length||0}} prévias</p>
      </div>

      <figure class="pipeline-video">
        <video v-if="sourceUrl" :src="sourceUrl" controls preload="metadata" playsinline aria-label="Vídeo original em miniatura"></video>
        <div v-else class="pipeline-video-empty">{{project.source?'Vídeo indisponível':importRecovery?'Importação interrompida':processing&&job?.progress?.steps.import==='running'?'Importando vídeo…':'Vídeo ainda não importado'}}</div>
        <figcaption>Vídeo original · {{project.source?'Fonte preservada':'Aguardando fonte'}}</figcaption>
      </figure>
    </header>

    <!-- ESTEIRA LINEAR DE PROGRESSO VISUAL (6 ETAPAS INTERATIVAS) -->
    <section class="stepper-track-wrap" aria-label="Esteira de progresso das etapas">
      <div class="stepper-track-title">
        <strong>Esteira de Processamento</strong>
        <span>{{names.filter(([id])=>state(id)==='completed').length}} de {{names.length}} etapas concluídas</span>
      </div>
      <div class="stepper-track">
        <template v-for="([id,title],idx) in names" :key="id">
          <div class="stepper-node" :data-stepper-stage="id" :data-state="state(id)" :class="{clickable:state(id)==='completed'}" @click="handleStepClick(id)">
            <div class="node-circle">
              <Check v-if="state(id)==='completed'" :size="15"/>
              <LoaderCircle v-else-if="['running','cancelling','processing'].includes(state(id))" class="spin" :size="15"/>
              <AlertCircle v-else-if="['failed','cancelled','interrupted'].includes(state(id))" :size="15"/>
              <span v-else>{{idx+1}}</span>
            </div>
            <span class="node-label">{{title}}</span>
            <small class="node-subtext">{{state(id)==='waiting'?'Próxima ação':labels[state(id)]||state(id)}}</small>
          </div>
          <div v-if="idx<names.length-1" class="stepper-connector" :class="{done:state(id)==='completed'}"></div>
        </template>
      </div>
    </section>

    <!-- CARD CONTEXTUAL HERO: A PRÓXIMA AÇÃO CLARA PARA O USUÁRIO -->
    <div class="action-hero-card" :data-action-state="activeAction">
      <div class="hero-card-content">
        <div class="hero-badge">Próxima Ação Recomendada</div>
        <template v-if="activeAction==='import-failed'">
          <h3>A importação do vídeo foi interrompida</h3>
          <p>O link do YouTube pode ter sido bloqueado ou o arquivo está inacessível. Escolha uma alternativa para prosseguir.</p>
        </template>
        <template v-else-if="activeAction==='transcribe'">
          <h3>Transcrever áudio original com Whisper</h3>
          <p>O vídeo está pronto. Gere a transcrição completa com marcação temporal precisa usando o processamento local.</p>
          <div class="hero-actions">
            <AppButton class="button primary hero-primary-btn" :disabled="busy||!project.source||processing" @click="$emit('transcribe')">
              <Play :size="15"/>Transcrever vídeo agora
            </AppButton>
          </div>
        </template>
        <template v-else-if="activeAction==='analyze'">
          <h3>Identificar temas e propostas com IA Gemini</h3>
          <p>A transcrição com {{project.word_count.toLocaleString('pt-BR')}} palavras está concluída. Encontre os trechos com maior potencial de retenção.</p>
          <div class="hero-actions">
            <AppButton class="button primary hero-primary-btn" :disabled="busy||processing" @click="$emit('analyze')">
              <Sparkles :size="15"/>{{project.has_analysis?'Nova análise de temas':recovery?'Continuar análise':'Iniciar análise inteligente'}}
            </AppButton>
          </div>
        </template>
        <template v-else-if="activeAction==='choose'">
          <h3>Curadoria editorial de cortes pronta</h3>
          <p>A IA encontrou {{analysis?.proposals.length||0}} trechos e {{analysis?.topic_groups.length||0}} temas. Selecione os melhores cortes sem sobreposição.</p>
          <div class="hero-actions">
            <AppButton class="button primary hero-primary-btn" :disabled="busy" @click="$emit('analysis')">
              <Scissors :size="15"/>Abrir Curadoria e Selecionar Cortes
            </AppButton>
          </div>
        </template>
        <template v-else-if="activeAction==='render'">
          <h3>{{selectedCount}} trecho(s) selecionado(s) para renderização</h3>
          <p>Seus cortes selecionados estão prontos para virar vídeos verticais 9:16 com enquadramento inteligente e legendas.</p>
          <div class="hero-actions">
            <AppButton class="button primary hero-primary-btn" :disabled="busy||!selectedCount||!project.has_analysis" @click="$emit('generate')">
              <Film :size="15"/>Gerar {{selectedCount}} Prévia(s) Vertical(is)
            </AppButton>
            <AppButton class="button secondary" @click="$emit('analysis')">Ajustar seleção</AppButton>
          </div>
        </template>
        <template v-else-if="activeAction==='review'">
          <h3>{{revisions?.length||0}} corte(s) gerado(s) disponíveis para revisão</h3>
          <p>Assista aos vídeos verticais 9:16, faça ajustes finos nas legendas e baixe os arquivos finais para publicação.</p>
          <div class="hero-actions">
            <AppButton class="button primary hero-primary-btn" @click="$emit('review')">
              <Play :size="15"/>Abrir Estúdio de Revisão 9:16
            </AppButton>
            <AppButton v-if="approved" class="button secondary" :disabled="busy" @click="$emit('export')">
              <Download :size="15"/>Exportar prontos
            </AppButton>
          </div>
        </template>
      </div>
    </div>

    <!-- GRUPOS DE ETAPAS DETALHADAS -->
    <div class="preparation-groups">
      <section v-for="group in groups" :key="group.title" class="preparation-group">
        <header>
          <h3>{{group.title}}</h3>
          <p>{{group.description}}</p>
        </header>
        <ol class="pipeline-steps">
          <li v-for="[id,title] in group.steps" :key="id" class="pipeline-step" :data-stage="id" :data-state="state(id)">
            <span class="step-mark" :class="{done:state(id)==='completed'}">
              <Check v-if="state(id)==='completed'" :size="16"/>
              <span v-else>{{names.findIndex(n=>n[0]===id)+1}}</span>
            </span>
            <div class="step-copy">
              <div class="step-heading">
                <h3>{{title}}</h3>
                <p>{{state(id)==='waiting'?'Sua próxima ação':labels[state(id)]||state(id)}}</p>
              </div>
              <div v-if="!['pending','waiting'].includes(state(id))" role="progressbar" :aria-label="title" :aria-valuenow="state(id)==='completed'?100:undefined" aria-valuemin="0" aria-valuemax="100" class="stage-progress" :class="{indeterminate:['running','processing','cancelling'].includes(state(id)),complete:state(id)==='completed',failed:['failed','cancelled','interrupted'].includes(state(id))}"><span></span></div>
              <div v-if="id==='import'&&importRecovery&&job" class="import-recovery">
                <p>Importação interrompida. Escolha como continuar.</p>
                <AppButton v-if="job.error" type="button" class="text-button" data-action="error-details" @click="notifyJob(job,true)">Ver motivo da falha</AppButton>
                <div class="step-actions">
                  <AppButton class="button small primary" data-action="retry-import" :disabled="busy||processing" @click="$emit('resume',job.id)"><RotateCcw :size="14"/>Tentar novamente</AppButton>
                  <AppButton class="button small secondary" data-action="replace-source" :disabled="busy||processing" @click="$emit('replaceSource',job.id)">Usar arquivo local</AppButton>
                </div>
              </div>
              <AppButton v-if="id==='transcribe'&&!project.has_transcript&&!project.is_manual&&!processing" class="button small secondary" :disabled="busy||!project.source" @click="$emit('transcribe')">Transcrever vídeo</AppButton>
              <AppButton v-if="id==='analyze'&&!project.is_manual&&!processing&&project.has_transcript" class="button small secondary" :disabled="busy" @click="$emit('analyze')">{{project.has_analysis?'Nova análise':recovery?'Continuar análise':'Iniciar análise'}}</AppButton>
              <AppButton v-if="id==='choose'&&!project.is_manual" class="button small secondary" :disabled="busy||!project.has_analysis" @click="$emit('render')">{{selectedCount?selectedCount+' trechos selecionados · Ajustar':'Escolher trechos'}}</AppButton>
              <AppButton v-if="id==='render'&&!project.is_manual" class="button small primary" :disabled="busy||!selectedCount||!project.has_analysis" @click="$emit('generate')">Gerar prévias</AppButton>
              <AppButton v-if="id==='export'&&approved" class="button small primary" :disabled="busy" @click="$emit('export')">Exportar prontos</AppButton>
            </div>
          </li>
        </ol>
      </section>
    </div>

    <!-- RESUMO DA ANÁLISE SE TRANSCRITO -->
    <div class="analysis-overview" v-if="project.has_transcript">
      <div>
        <strong>{{analysis?.state==='completed'?'Análise concluída':analysis?.proposals.length?'Análise parcial disponível':'Acompanhe a análise'}}</strong>
        <p v-if="analysis">{{analysis.completed_windows}}/{{analysis.total_windows}} janelas · {{analysis.topic_groups.length}} temas · {{analysis.proposals.length}} propostas</p>
      </div>
      <AppButton class="button small secondary" @click="$emit('analysis')">Ver análise</AppButton>
    </div>

    <!-- ATIVIDADE RECENTE DO MOTOR -->
    <div v-if="job&&!importRecovery" class="pipeline-activity" aria-live="polite">
      <p v-if="['analyze','prepare'].includes(job.operation)&&project.has_transcript">{{job.requests_used||0}} chamada(s) Gemini{{job.request_mode==='automatic'?' · planejamento automático':' de '+job.request_limit}}</p>
      <AppButton v-if="job.error" type="button" class="text-button" @click="notifyJob(job,true)">Ver motivo da falha</AppButton>
      <p v-if="job.exports?.length">{{job.exports.length}} pacote(s) exportado(s).</p>
      <AppButton v-if="recovery&&!['analyze','render'].includes(job.operation)" class="button small secondary" :disabled="busy||processing" @click="$emit('resume',job.id)"><RotateCcw :size="14"/>Continuar preparação</AppButton>
    </div>

    <AppButton v-if="project.error&&!job" type="button" class="text-button" @click="notify.error(project.error.message)">Ver motivo da falha</AppButton>
    <footer class="pipeline-note">Preparação automática até a análise. Geração e download sob seu controle.</footer>
  </section>
</template>

<style scoped>
.pipeline-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preparation-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 20px;
  align-items: center;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border-subtle, var(--line));
}

.pipeline-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.pipeline-video {
  margin: 0;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--color-border-subtle, var(--line));
  background: #000;
  display: flex;
  flex-direction: column;
}

.pipeline-video video {
  width: 100%;
  aspect-ratio: 16/9;
  display: block;
  object-fit: cover;
}

.pipeline-video-empty {
  width: 100%;
  aspect-ratio: 16/9;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  text-align: center;
  font-size: 0.8rem;
  color: var(--color-text-muted, var(--muted));
  background: var(--color-surface-hover, var(--soft));
}

.pipeline-video figcaption {
  font-size: 0.72rem;
  padding: 6px 10px;
  background: var(--color-surface, var(--panel));
  color: var(--color-text-muted, var(--muted));
  border-top: 1px solid var(--color-border-subtle, var(--line));
}

.stepper-track-wrap {
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: 14px;
  padding: 14px 18px;
}

.stepper-track-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.stepper-track-title strong {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--color-text-primary, var(--ink));
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stepper-track-title span {
  font-size: 0.8rem;
  color: var(--color-text-muted, var(--muted));
}

.stepper-track {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  gap: 8px;
}

.stepper-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  position: relative;
  z-index: 2;
  flex: 1;
  text-align: center;
  background: transparent;
  border: none;
  padding: 0;
}

.stepper-node.clickable {
  cursor: pointer;
}

.node-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.82rem;
  font-weight: 600;
  background: var(--color-surface-raised, var(--soft));
  color: var(--color-text-muted, var(--muted));
  border: 2px solid var(--color-border-subtle, var(--line));
  transition: all 0.2s ease;
}

.stepper-node[data-state="completed"] .node-circle {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  border-color: #10b981;
}

.stepper-node[data-state="running"] .node-circle,
.stepper-node[data-state="processing"] .node-circle {
  background: var(--color-accent-soft, var(--accent-soft));
  color: var(--color-accent, var(--accent));
  border-color: var(--color-accent, var(--accent));
  box-shadow: 0 0 0 4px rgba(217, 119, 36, 0.2);
}

.stepper-node[data-state="waiting"] .node-circle {
  background: var(--color-surface, var(--panel));
  color: var(--color-accent, var(--accent));
  border-color: var(--color-accent, var(--accent));
  font-weight: 700;
}

.stepper-node[data-state="failed"] .node-circle,
.stepper-node[data-state="cancelled"] .node-circle,
.stepper-node[data-state="interrupted"] .node-circle {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border-color: #ef4444;
}

.node-label {
  font-size: 0.77rem;
  font-weight: 600;
  color: var(--color-text-primary, var(--ink));
}

.node-subtext {
  font-size: 0.68rem;
  color: var(--color-text-muted, var(--muted));
}

.stepper-connector {
  flex: 1;
  height: 2px;
  background: var(--color-border-subtle, var(--line));
  margin-top: -18px;
  z-index: 1;
}

.stepper-connector.done {
  background: #10b981;
}

.action-hero-card {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(217, 119, 36, 0.06) 100%);
  border: 1px solid var(--color-accent, rgba(99, 102, 241, 0.3));
  border-radius: 14px;
  padding: 18px 22px;
}

.hero-badge {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-accent, #6366f1);
  margin-bottom: 6px;
}

.hero-card-content h3 {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--color-text-primary, var(--ink));
  margin: 0 0 6px;
}

.hero-card-content p {
  font-size: 0.83rem;
  color: var(--color-text-secondary, var(--muted));
  margin: 0 0 14px;
  max-width: 72ch;
  line-height: 1.5;
}

.hero-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.hero-primary-btn {
  font-size: 0.88rem;
  font-weight: 600;
  padding: 9px 18px;
}

@media (max-width: 800px) {
  .preparation-header {
    grid-template-columns: 1fr;
  }
  .stepper-track {
    flex-wrap: wrap;
    gap: 12px;
  }
  .stepper-connector {
    display: none;
  }
}
</style>