<script setup lang="ts">
import {computed,ref} from 'vue'
import AppButton from './AppButton.vue'
import {ListOrdered,X,ArrowUpRight,Square,CheckCircle2,AlertCircle,LoaderCircle} from '@lucide/vue'
import type {Job,Project} from '../types'
import {active,labels,stages} from '../format'

const props=defineProps<{jobs:Job[];projects:Project[];busy:boolean}>()
const emit=defineEmits<{cancel:[id:string];open:[projectId:string];close:[]}>()
const filter=ref<'active'|'all'>('active')

const projectMap=computed(()=>{
  const map=new Map<string,Project>()
  for(const p of props.projects)map.set(p.id,p)
  return map
})

const activeJobs=computed(()=>props.jobs.filter(j=>active(j.status)).sort((a,b)=>a.created_at.localeCompare(b.created_at)))
const recentJobs=computed(()=>[...props.jobs].sort((a,b)=>b.created_at.localeCompare(a.created_at)).slice(0,20))
const displayJobs=computed(()=>filter.value==='active'?activeJobs.value:recentJobs.value)

const runningCount=computed(()=>props.jobs.filter(j=>j.status==='running').length)
const pendingCount=computed(()=>props.jobs.filter(j=>j.status==='pending').length)

function projectName(pid:string):string{
  const p=projectMap.value.get(pid)
  return p?.title||p?.name||'Projeto '+pid.slice(0,8)
}

function handleKey(e:KeyboardEvent){
  if(e.key==='Escape')emit('close')
}
</script>

<template>
  <div class="global-queue-overlay" role="dialog" aria-modal="true" aria-labelledby="queue-modal-title" @keydown="handleKey" @click.self="$emit('close')">
    <div class="global-queue-container">
      <header class="queue-modal-header">
        <div class="queue-title-area">
          <span class="queue-icon-wrapper"><ListOrdered :size="20"/></span>
          <div>
            <h2 id="queue-modal-title">Fila Global de Tarefas</h2>
            <p>{{runningCount}} em execução · {{pendingCount}} aguardando em todos os projetos</p>
          </div>
        </div>
        <div class="queue-header-actions">
          <div class="queue-tabs" role="tablist">
            <AppButton class="queue-tab" :class="{selected:filter==='active'}" @click="filter='active'">Ativas ({{activeJobs.length}})</AppButton>
            <AppButton class="queue-tab" :class="{selected:filter==='all'}" @click="filter='all'">Histórico recente</AppButton>
          </div>
          <AppButton class="icon-button close-btn" title="Fechar fila global" aria-label="Fechar" @click="$emit('close')"><X :size="18"/></AppButton>
        </div>
      </header>

      <section class="queue-modal-body hidden-scrollbar">
        <div v-if="displayJobs.length" class="queue-jobs-list">
          <article v-for="job in displayJobs" :key="job.id" class="queue-job-card" :data-status="job.status">
            <div class="job-card-top">
              <div class="job-project-tag">
                <AppButton class="project-jump-btn" title="Abrir este projeto" @click="$emit('open',job.project_id)">
                  <strong>{{projectName(job.project_id)}}</strong>
                  <ArrowUpRight :size="14"/>
                </AppButton>
              </div>
              <div class="job-status-tags">
                <span class="status-pill" :data-status="job.status">
                  <LoaderCircle v-if="job.status==='running'" class="spin" :size="12"/>
                  <CheckCircle2 v-else-if="job.status==='completed'" :size="12"/>
                  <AlertCircle v-else-if="['failed','interrupted'].includes(job.status)" :size="12"/>
                  {{labels[job.status]||job.status}}
                </span>
                <span v-if="job.status==='pending'" class="queue-position-pill">Posição {{job.queue_position||'—'}}</span>
              </div>
            </div>

            <div class="job-card-details">
              <div class="job-op-title">
                <span>Operação:</span>
                <strong>{{stages[job.stage||job.operation]||job.operation}}</strong>
              </div>

              <div v-if="job.status==='pending'" class="job-pending-note">
                <small>{{job.queue_reason||'Aguardando liberação de worker…'}}</small>
              </div>

              <div v-else-if="job.status==='running'" class="job-progress-info">
                <div class="progress-bar-wrap" role="progressbar" aria-label="Progresso da tarefa">
                  <div class="progress-bar-fill indeterminate"></div>
                </div>
                <small v-if="job.progress?.total_items">{{job.progress.completed_items||0}} de {{job.progress.total_items}} itens prontos</small>
                <small v-else-if="job.requests_used">{{job.requests_used}} chamadas realizadas</small>
              </div>

              <div v-else-if="job.error" class="job-error-note">
                <small>{{job.error.message}}</small>
              </div>
            </div>

            <div v-if="active(job.status)" class="job-card-footer">
              <AppButton class="button small secondary cancel-job-btn" :disabled="busy||job.status==='cancelling'" @click="$emit('cancel',job.id)">
                <Square :size="12"/>{{job.status==='pending'?'Remover da fila':'Cancelar tarefa'}}
              </AppButton>
            </div>
          </article>
        </div>

        <div v-else class="queue-empty-state">
          <ListOrdered :size="38"/>
          <h3>{{filter==='active'?'Nenhuma tarefa em execução':'Nenhum histórico disponível'}}</h3>
          <p>{{filter==='active'?'Quando você iniciar importação, transcrição ou geração, as tarefas aparecerão aqui.':'Nenhuma tarefa recente foi registrada na sessão.'}}</p>
        </div>
      </section>

      <footer class="queue-modal-footer">
        <span class="queue-hint">O motor gerencia até 2 tarefas simultâneas com trava de API Gemini para evitar concorrência.</span>
        <AppButton class="button secondary" @click="$emit('close')">Fechar</AppButton>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.global-queue-overlay {
  position: fixed;
  inset: 0;
  background: rgba(14, 16, 19, 0.75);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}
.global-queue-container {
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: 16px;
  width: 100%;
  max-width: 680px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 35px rgba(0, 0, 0, 0.5);
  overflow: hidden;
}
.queue-modal-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border-subtle, var(--line));
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: var(--color-surface-raised, var(--soft));
}
.queue-title-area {
  display: flex;
  align-items: center;
  gap: 12px;
}
.queue-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--color-accent-soft, var(--accent-soft));
  color: var(--color-accent, var(--accent));
}
.queue-title-area h2 {
  font-size: 1.1rem;
  margin: 0;
  color: var(--color-text-primary, var(--ink));
}
.queue-title-area p {
  font-size: 0.8rem;
  margin: 2px 0 0;
  color: var(--color-text-muted, var(--muted));
}
.queue-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.queue-tabs {
  display: flex;
  gap: 4px;
  background: var(--color-canvas, #0e1013);
  padding: 3px;
  border-radius: 8px;
}
.queue-tab {
  font-size: 0.78rem;
  min-height: 30px;
  padding: 5px 12px;
  border-radius: 6px;
  background: transparent;
  border: none;
  color: var(--color-text-muted, var(--muted));
  cursor: pointer;
  display: inline-flex;
  align-items: center;
}
.queue-tab.selected {
  background: var(--color-surface, var(--panel));
  color: var(--color-accent, var(--accent));
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}
.queue-modal-body {
  padding: 16px 20px;
  overflow-y: auto;
  flex: 1;
}
.queue-jobs-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.queue-job-card {
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: 12px;
  padding: 14px 16px;
  background: var(--color-surface-raised, var(--soft));
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: border-color 0.15s ease;
}
.queue-job-card[data-status="running"] {
  border-left: 4px solid var(--color-accent, var(--accent));
}
.queue-job-card[data-status="pending"] {
  border-left: 4px solid var(--color-warning-border, #8c531b);
}
.job-card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}
.project-jump-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
  background: transparent;
  border: none;
  color: var(--color-accent, var(--accent));
  padding: 4px 8px;
  cursor: pointer;
  border-radius: 6px;
  font-size: 0.88rem;
}
.project-jump-btn:hover {
  text-decoration: underline;
  background: var(--color-accent-soft, var(--accent-soft));
}
.job-status-tags {
  display: flex;
  align-items: center;
  gap: 6px;
}
.queue-position-pill {
  font-size: 0.75rem;
  padding: 3px 9px;
  border-radius: 999px;
  background: var(--color-warning-surface, #2a2012);
  color: var(--color-warning-text, #fbbf24);
  border: 1px solid var(--color-warning-border, #8c531b);
}
.job-card-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 0.85rem;
}
.job-op-title {
  display: flex;
  gap: 8px;
  align-items: center;
  color: var(--color-text-primary, var(--ink));
}
.job-op-title span {
  color: var(--color-text-muted, var(--muted));
}
.job-pending-note small {
  color: var(--color-text-muted, var(--muted));
}
.job-error-note small {
  color: var(--color-error, #ef4444);
}
.progress-bar-wrap {
  height: 6px;
  background: var(--color-canvas, #0e1013);
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 4px;
}
.progress-bar-fill.indeterminate {
  height: 100%;
  width: 50%;
  background: var(--color-accent, var(--accent));
  border-radius: 999px;
  animation: indeterminate-progress 1.5s infinite ease-in-out;
}
@keyframes indeterminate-progress {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(250%); }
}
.job-card-footer {
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid var(--color-border-subtle, var(--line));
  padding-top: 8px;
}
.queue-empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--color-text-muted, var(--muted));
}
.queue-empty-state h3 {
  margin: 12px 0 6px;
  color: var(--color-text-primary, var(--ink));
}
.queue-empty-state p {
  margin: 0;
  font-size: 0.85rem;
}
.queue-modal-footer {
  padding: 12px 20px;
  border-top: 1px solid var(--color-border-subtle, var(--line));
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--color-surface-raised, var(--soft));
  font-size: 0.78rem;
  color: var(--color-text-muted, var(--muted));
}
</style>
