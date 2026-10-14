<script setup lang="ts">
import { computed, ref, toRef } from 'vue';
import AppButton from './AppButton.vue';
import { ElScrollbar, ElTag, ElProgress, ElEmpty, ElCard } from 'element-plus';
import {
  ListOrdered,
  X,
  ArrowUpRight,
  Square,
  CheckCircle2,
  AlertCircle,
  LoaderCircle,
  Trash2,
} from '@lucide/vue';
import type { Job, Project } from '../types';
import { active, labels, stages } from '../format';
import { useJobQueue } from '../composables/useJobQueue';

const props = defineProps<{ jobs: Job[]; projects: Project[]; busy: boolean }>();
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
    <div class="global-queue-container">
      <header class="queue-modal-header">
        <div class="queue-title-area">
          <span class="queue-icon-wrapper"><ListOrdered :size="20" /></span>
          <div>
            <h2 id="queue-modal-title">Fila Global de Tarefas</h2>
            <p>
              {{ runningCount }} em execução · {{ pendingCount }} aguardando em todos os projetos
            </p>
          </div>
        </div>
        <div class="queue-header-actions">
          <div class="queue-tabs" role="tablist">
            <AppButton
              class="queue-tab"
              :class="{ selected: filter === 'active' }"
              @click="filter = 'active'"
              >Ativas ({{ activeJobs.length }})</AppButton
            >
            <AppButton
              class="queue-tab"
              :class="{ selected: filter === 'all' }"
              @click="filter = 'all'"
              >Histórico recente</AppButton
            >
            <AppButton
              v-if="filter === 'all' && recentJobs.length > 0"
              class="queue-tab queue-clear-action"
              title="Limpar tarefas concluídas ou falhadas"
              :disabled="busy"
              @click="$emit('clearHistory')"
              ><Trash2 :size="14" style="margin-right: 4px" />Limpar histórico</AppButton
            >
          </div>
          <AppButton
            class="icon-button close-btn"
            title="Fechar fila global"
            aria-label="Fechar"
            @click="$emit('close')"
            ><X :size="18"
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
                  <ArrowUpRight :size="14" />
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
                  <LoaderCircle v-if="job.status === 'running'" class="spin" :size="12" />
                  <CheckCircle2 v-else-if="job.status === 'completed'" :size="12" />
                  <AlertCircle
                    v-else-if="['failed', 'interrupted'].includes(job.status)"
                    :size="12"
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

              <div v-else-if="job.status === 'running'" class="job-progress-info">
                <el-progress
                  :percentage="
                    job.progress?.total_items
                      ? Math.round(
                          ((job.progress.completed_items || 0) / job.progress.total_items) * 100
                        )
                      : 100
                  "
                  :indeterminate="!job.progress?.total_items"
                  :color="'#ECEEF0'"
                  :stroke-width="4"
                  :show-text="false"
                  style="margin-bottom: 6px"
                />
                <small v-if="job.progress?.total_items"
                  >{{ job.progress.completed_items || 0 }} de {{ job.progress.total_items }} itens
                  prontos</small
                >
                <small v-else-if="job.requests_used"
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
                :disabled="busy || job.status === 'cancelling'"
                @click="$emit('cancel', job.id)"
              >
                <Square :size="12" />{{
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
            <ListOrdered :size="40" style="color: var(--color-text-muted, #9aa4b2)" />
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
  padding: 14px 4px;
  border-bottom: 1px solid var(--color-border-subtle, rgba(255, 255, 255, 0.06));
  background: transparent;
}
.queue-job-row:last-child,
.queue-job-card:last-child {
  border-bottom: none;
}
.queue-clear-action {
  margin-left: 8px;
  color: #ef4444 !important;
}
.job-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}
.project-jump-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: 0;
  color: var(--color-text-primary, var(--ink));
  font-size: 0.88rem;
  cursor: pointer;
  padding: 0;
}
.project-jump-btn:hover {
  color: var(--color-text-primary);
  text-decoration: underline;
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
  gap: 8px;
  font-size: 0.82rem;
}
.job-op-title {
  display: flex;
  gap: 6px;
}
.job-op-title span {
  color: var(--color-text-secondary, var(--muted));
}
.job-op-title strong {
  color: var(--color-text-primary, var(--ink));
}
.job-pending-note small {
  color: var(--color-text-secondary, var(--muted));
}
.job-error-note small {
  color: var(--color-danger-text, #f87171);
}
.job-card-footer {
  margin-top: 12px;
  padding-top: 10px;
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
