<script setup lang="ts">
import { computed, ref, toRef } from 'vue';
import AppButton from './AppButton.vue';
import AppIcon from './ui/AppIcon.vue';
import ProcessProgress from './ui/ProcessProgress.vue';
import { ElScrollbar, ElTag, ElEmpty, ElCard } from 'element-plus';
import type { Job, Project } from '../types';
import { active, labels, stages } from '../format';
import { useJobQueue } from '../composables/useJobQueue';
import { useModalFocus } from '../composables/useModalFocus';
const modalRoot = ref<HTMLElement>();
useModalFocus(modalRoot);

const props = defineProps<{
  jobs: Job[];
  projects: Project[];
  busy: boolean;
  pendingJobIds?: string[];
}>();
const emit = defineEmits<{
  cancel: [id: string];
  open: [projectId: string];
  close: [];
  clearHistory: [];
}>();
const filter = ref<'active' | 'all'>('active');

const projectMap = computed(() => {
  const map = new Map<string, Project>();
  for (const p of props.projects) map.set(p.id, p);
  return map;
});

const { activeJobs, recentJobs, runningCount, pendingCount } = useJobQueue(toRef(props, 'jobs'));

const displayJobs = computed(() =>
  filter.value === 'active' ? activeJobs.value : recentJobs.value
);

function projectName(pid: string): string {
  const p = projectMap.value.get(pid);
  const name = p?.title || p?.name;
  if (!name || /^[0-9a-f]{8}-[0-9a-f]{4}/i.test(name) || /^[0-9a-f]{16,}/i.test(name)) {
    return 'Projeto finalizado';
  }
  return name;
}

function handleKey(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close');
}

function tagType(status: string): 'primary' | 'success' | 'warning' | 'danger' | 'info' {
  if (status === 'completed') return 'success';
  if (status === 'running') return 'warning';
  if (['failed', 'interrupted', 'rejected'].includes(status)) return 'danger';
  if (status === 'pending') return 'info';
  return 'info';
}
</script>

<template>
  <div
    class="global-queue-overlay"
    role="dialog"
    aria-modal="true"
    aria-labelledby="queue-modal-title"
    @keydown="handleKey"
    @click.self="$emit('close')"
  >
    <div ref="modalRoot" class="global-queue-container" tabindex="-1">
      <header class="queue-modal-header">
        <div class="queue-title-area">
          <span class="queue-icon-wrapper"><AppIcon name="queue" /></span>
          <div>
            <h2 id="queue-modal-title">Fila Global de Tarefas</h2>
            <p>
              {{ runningCount }} em execução · {{ pendingCount }} aguardando em todos os projetos
            </p>
          </div>
        </div>
        <div class="queue-header-actions">
          <div class="queue-tabs" role="group" aria-label="Filtrar tarefas">
            <AppButton
              class="queue-tab"
              :class="{ selected: filter === 'active' }"
              :aria-pressed="filter === 'active'"
              @click="filter = 'active'"
              >Ativas ({{ activeJobs.length }})</AppButton
            >
            <AppButton
              class="queue-tab"
              :class="{ selected: filter === 'all' }"
              :aria-pressed="filter === 'all'"
              @click="filter = 'all'"
              >Histórico recente</AppButton
            >
            <AppButton
              v-if="filter === 'all' && recentJobs.length > 0"
              class="queue-tab queue-clear-action"
              title="Remover tarefas concluídas e seus arquivos temporários; preservar tarefas que podem ser retomadas"
              :disabled="busy"
              @click="$emit('clearHistory')"
              ><AppIcon name="trash" size="sm" style="margin-right: 4px" />Limpar
              concluídas</AppButton
            >
          </div>
          <AppButton
            class="icon-button close-btn"
            title="Fechar fila global"
            aria-label="Fechar"
            @click="$emit('close')"
            ><AppIcon name="close"
          /></AppButton>
        </div>
      </header>

      <el-scrollbar class="queue-modal-body" max-height="65vh">
        <div v-if="displayJobs.length" class="queue-jobs-list">
          <div
            v-for="job in displayJobs"
            :key="job.id"
            class="queue-job-row"
            :data-status="job.status"
          >
            <div class="job-card-top">
              <div class="job-project-tag">
                <AppButton
                  class="project-jump-btn"
                  title="Abrir este projeto"
                  @click="$emit('open', job.project_id)"
                >
                  <strong>{{ projectName(job.project_id) }}</strong>
                  <AppIcon name="open-external" size="sm" />
                </AppButton>
              </div>
              <div class="job-status-tags">
                <el-tag
                  :type="tagType(job.status)"
                  effect="dark"
                  size="small"
                  class="status-pill"
                  :data-status="job.status"
                >
                  <AppIcon v-if="job.status === 'running'" name="spinner" size="sm" class="spin" />
                  <AppIcon v-else-if="job.status === 'completed'" name="check-circle" size="sm" />
                  <AppIcon
                    v-else-if="['failed', 'interrupted'].includes(job.status)"
                    name="warning"
                    size="sm"
                  />
                  {{ labels[job.status] || job.status }}
                </el-tag>
                <el-tag
                  v-if="job.status === 'pending'"
                  type="info"
                  size="small"
                  class="queue-position-pill"
                >
                  Posição {{ job.queue_position || '—' }}
                </el-tag>
              </div>
            </div>

            <div class="job-card-details">
              <div class="job-op-title">
                <span>Operação:</span>
                <strong>{{ stages[job.stage || job.operation] || job.operation }}</strong>
              </div>

              <div v-if="job.status === 'pending'" class="job-pending-note">
                <small>{{ job.queue_reason || 'Aguardando liberação de worker…' }}</small>
              </div>

              <div
                v-else-if="['running', 'cancelling'].includes(job.status)"
                class="job-progress-info"
              >
                <ProcessProgress
                  :progress="job.progress"
                  :status="job.status"
                  :started-at="job.started_at"
                  :finished-at="job.finished_at"
                />
                <small v-if="!job.progress?.total_items && job.requests_used"
                  >{{ job.requests_used }} chamadas realizadas</small
                >
              </div>

              <div v-else-if="job.error" class="job-error-note">
                <small>{{ job.error.message }}</small>
              </div>
            </div>

            <div v-if="active(job.status)" class="job-card-footer">
              <AppButton
                class="button small secondary cancel-job-btn"
                :disabled="pendingJobIds?.includes(job.id) || job.status === 'cancelling'"
                @click="$emit('cancel', job.id)"
              >
                <AppIcon name="stop" size="sm" />{{
                  job.status === 'pending' ? 'Remover da fila' : 'Cancelar tarefa'
                }}
              </AppButton>
            </div>
          </div>
        </div>

        <el-empty
          v-else
          :description="
            filter === 'active' ? 'Nenhuma tarefa em execução' : 'Nenhum histórico disponível'
          "
          class="queue-empty-state"
        >
          <template #image>
            <AppIcon name="queue" size="lg" />
          </template>
          <p>
            {{
              filter === 'active'
                ? 'Tarefas em execução ou pendentes aparecerão aqui.'
                : 'Nenhuma tarefa recente no histórico.'
            }}
          </p>
        </el-empty>
      </el-scrollbar>

      <footer class="queue-modal-footer">
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
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}
.global-queue-container {
  outline: none;
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: var(--radius-panel);
  width: 100%;
  max-width: 680px;
  max-height: calc(100dvh - 32px);
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 35px rgba(0, 0, 0, 0.5);
  overflow: hidden;
}
.queue-modal-header {
  flex-wrap: wrap;
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
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: var(--color-surface-selected);
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border-subtle);
}
.queue-title-area h2 {
  font-size: 1.15rem;
  font-weight: 600;
  margin: 0;
  color: var(--color-text-primary, var(--ink));
}
.queue-title-area p {
  font-size: 0.8rem;
  color: var(--color-text-secondary, var(--muted));
  margin: 2px 0 0;
}
.queue-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.queue-tabs {
  display: flex;
  background: var(--color-canvas, #0e1013);
  padding: 3px;
  border-radius: 8px;
  border: 1px solid var(--color-border-subtle, var(--line));
}
.queue-tab {
  background: transparent;
  border: 0;
  color: var(--color-text-secondary, var(--muted));
  font-size: 0.8rem;
  font-weight: 500;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.queue-tab.selected {
  background: var(--color-surface, var(--panel));
  color: var(--color-text-primary);
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}
.queue-modal-body {
  padding: 18px 20px;
  flex: 1;
}
.queue-jobs-list {
  display: flex;
  flex-direction: column;
}
.queue-job-row,
.queue-job-card {
  padding: 16px 18px;
  border-radius: var(--radius-panel, 8px);
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  margin-bottom: 12px;
  transition: all 0.2s ease;
}
.queue-job-row:last-child,
.queue-job-card:last-child {
  margin-bottom: 0;
}
.queue-job-row:hover {
  border-color: var(--color-border-strong);
}
.queue-job-row[data-status='running'] {
  border-color: rgba(175, 198, 213, 0.4);
  background: rgba(175, 198, 213, 0.04);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.18);
}
.queue-clear-action {
  margin-left: 8px;
  color: var(--color-danger);
}
.job-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.project-jump-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--color-canvas);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-control, 6px);
  color: var(--color-text-primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  padding: 5px 12px;
  transition: all 0.15s ease;
}
.project-jump-btn:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-border-strong);
  color: var(--color-action-primary);
}
.job-status-tags {
  display: flex;
  align-items: center;
  gap: 8px;
}
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
}
.queue-position-pill {
  background: var(--color-canvas, #0e1013);
  border-color: var(--color-border-subtle, var(--line));
}
.job-card-details {
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-size: 0.85rem;
}
.job-op-title {
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.job-op-title span {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary);
}
.job-op-title strong {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}
.job-pending-note small {
  color: var(--color-text-secondary, var(--muted));
  font-size: 12px;
}
.job-error-note small {
  color: var(--color-danger-text, #f87171);
  font-size: 12px;
}
.job-card-footer {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border-subtle, var(--line));
  display: flex;
  justify-content: flex-end;
}
.queue-empty-state {
  padding: 30px 20px;
  text-align: center;
}
.queue-empty-state p {
  color: var(--color-text-secondary, var(--muted));
  font-size: 0.85rem;
  max-width: 380px;
  margin: 8px auto 0;
}
.queue-modal-footer {
  padding: 14px 20px;
  border-top: 1px solid var(--color-border-subtle, var(--line));
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: var(--color-surface-raised, var(--soft));
}
.queue-hint {
  font-size: 0.78rem;
  color: var(--color-text-secondary, var(--muted));
}
</style>
