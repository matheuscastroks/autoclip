<script setup lang="ts">
import AppButton from './AppButton.vue';
import AppIcon from './ui/AppIcon.vue';
import { computed, ref, watch } from 'vue';
import {
  Search,
  Check,
  Scissors,
  FileText,
  RotateCcw,
  Sparkles,
  Clock,
  AlertTriangle,
  Volume2,
  Layers,
  Trash2,
  CheckCheck,
  X,
} from '@lucide/vue';
import type { AnalysisView, AnalysisSelection, Job, Proposal } from '../types';
import { time, analysisLabels } from '../format';
import { notify } from '../notifications';
import AnalysisFeedback from './AnalysisFeedback.vue';
import { useDiscardedProposals } from '../composables/useDiscardedProposals';
import { vRecoverMedia } from '../directives/recoverMedia';

const props = defineProps<{
  analysis: AnalysisView | null;
  selection: AnalysisSelection | null;
  jobs: Job[];
  sourceUrl: string;
  busy: boolean;
}>();
const emit = defineEmits<{
  generate: [value: { analysis_hash: string; candidate_ids: string[] }];
  selection: [value: AnalysisSelection];
  resume: [];
}>();
const topic = ref(''),
  search = ref(''),
  focused = ref(''),
  selected = ref<string[]>([]),
  player = ref<HTMLVideoElement>(),
  playEnd = ref(0);
const locallyEdited = ref(false);
const {
  discarded,
  loadDiscarded,
  saveDiscarded,
  discardItem,
  restoreItem,
  discardMany,
  restoreMany,
} = useDiscardedProposals();
const filterMode = ref<'active' | 'discarded' | 'all'>('active');

const analysisStateLabel = computed(
  () => analysisLabels[props.analysis?.state || 'not_started'] || 'Estado da análise'
);
const complete = computed(
  () => props.analysis?.state === 'completed' && !!props.analysis.analysis_hash
);
const proposals = computed(() => props.analysis?.proposals || []);
const activeProposals = computed(() =>
  proposals.value.filter(p => !discarded.value.includes(p.candidate_id))
);
const discardedProposals = computed(() =>
  proposals.value.filter(p => discarded.value.includes(p.candidate_id))
);

function isTopicDiscarded(groupId: string): boolean {
  const groupProps = proposals.value.filter(p => p.group_id === groupId);
  return groupProps.length > 0 && groupProps.every(p => discarded.value.includes(p.candidate_id));
}

const visibleTopicGroups = computed(() => {
  const all = props.analysis?.topic_groups || [];
  if (filterMode.value === 'discarded') {
    return all.filter(g => isTopicDiscarded(g.id));
  }
  if (filterMode.value === 'active') {
    return all.filter(g => !isTopicDiscarded(g.id));
  }
  return all;
});

const filtered = computed(() =>
  proposals.value.filter(p => {
    if (filterMode.value === 'active' && discarded.value.includes(p.candidate_id)) return false;
    if (filterMode.value === 'discarded' && !discarded.value.includes(p.candidate_id)) return false;
    if (topic.value && p.group_id !== topic.value) return false;
    if (search.value) {
      const q = search.value.toLocaleLowerCase('pt-BR');
      const target = [p.title, p.rationale, p.text].join(' ').toLocaleLowerCase('pt-BR');
      if (!target.includes(q)) return false;
    }
    return true;
  })
);

const current = computed(
  () => filtered.value.find(p => p.candidate_id === focused.value) || filtered.value[0]
);

function discard(id: string) {
  discardItem(id, props.analysis?.analysis_hash);
  if (selected.value.includes(id)) {
    selected.value = selected.value.filter(s => s !== id);
    locallyEdited.value = true;
    emit('selection', {
      schema_version: '1.0',
      analysis_hash: props.analysis!.analysis_hash,
      candidate_ids: [...validSelection.value],
    });
  }
  const targetProp = proposals.value.find(p => p.candidate_id === id);
  if (targetProp?.group_id && topic.value === targetProp.group_id) {
    if (isTopicDiscarded(targetProp.group_id)) {
      topic.value = '';
      focused.value = '';
    }
  }
}

function discardTopic(groupId: string) {
  const groupProps = proposals.value.filter(p => p.group_id === groupId);
  const ids = groupProps.map(p => p.candidate_id);
  discardMany(ids, props.analysis?.analysis_hash);
  selected.value = selected.value.filter(s => !ids.includes(s));
  locallyEdited.value = true;
  emit('selection', {
    schema_version: '1.0',
    analysis_hash: props.analysis!.analysis_hash,
    candidate_ids: [...validSelection.value],
  });
  if (topic.value === groupId) {
    topic.value = '';
    focused.value = '';
  }
  notify.info('Tema descartado.');
}

function restoreTopic(groupId: string) {
  const groupProps = proposals.value.filter(p => p.group_id === groupId);
  const ids = groupProps.map(p => p.candidate_id);
  restoreMany(ids, props.analysis?.analysis_hash);
  notify.info('Tema restaurado.');
}

function restore(id: string) {
  restoreItem(id, props.analysis?.analysis_hash);
}

function selectAllEligible() {
  if (!complete.value || props.busy) return;
  const toSelect: string[] = [];
  const candidates = proposals.value.filter(
    p =>
      p.eligible &&
      !discarded.value.includes(p.candidate_id) &&
      (!topic.value || p.group_id === topic.value)
  );
  for (const c of candidates) {
    const hasOverlap = toSelect.some(id => {
      const kept = proposals.value.find(p => p.candidate_id === id)!;
      return Math.min(c.end_us, kept.end_us) > Math.max(c.start_us, kept.start_us);
    });
    if (!hasOverlap) {
      toSelect.push(c.candidate_id);
    }
  }
  locallyEdited.value = true;
  selected.value = toSelect;
  emit('selection', {
    schema_version: '1.0',
    analysis_hash: props.analysis!.analysis_hash,
    candidate_ids: [...validSelection.value],
  });
  if (candidates.length > toSelect.length) {
    notify.info(
      `${toSelect.length} propostas selecionadas. Trechos sobrepostos foram desconsiderados.`
    );
  } else {
    notify.info(`${toSelect.length} propostas selecionadas.`);
  }
}

function clearSelection() {
  if (props.busy) return;
  locallyEdited.value = true;
  selected.value = [];
  emit('selection', {
    schema_version: '1.0',
    analysis_hash: props.analysis?.analysis_hash || '',
    candidate_ids: [],
  });
  notify.info('Seleção limpa.');
}

function overlapsWithSelected(p: Proposal): boolean {
  if (selected.value.includes(p.candidate_id)) return false;
  return validSelection.value.some(id => {
    const other = proposals.value.find(cand => cand.candidate_id === id);
    if (!other) return false;
    return Math.min(p.end_us, other.end_us) > Math.max(p.start_us, other.start_us);
  });
}

const validSelection = computed(() => {
  const result: string[] = [];
  for (const id of selected.value) {
    if (discarded.value.includes(id)) continue;
    const cand = proposals.value.find(p => p.candidate_id === id && p.eligible);
    if (!cand) continue;
    const hasOverlap = result.some(keptId => {
      const kept = proposals.value.find(p => p.candidate_id === keptId)!;
      return Math.min(cand.end_us, kept.end_us) > Math.max(cand.start_us, kept.start_us);
    });
    if (!hasOverlap) result.push(id);
  }
  return result;
});

const totalSelectedDurationUs = computed(() => {
  return validSelection.value.reduce((total, id) => {
    const cand = proposals.value.find(p => p.candidate_id === id);
    return total + (cand?.duration_us || 0);
  }, 0);
});

const overlap = computed(
  () =>
    selected.value.length !== validSelection.value.length ||
    validSelection.value.some((id, i) =>
      validSelection.value.slice(i + 1).some(other => {
        const a = proposals.value.find(p => p.candidate_id === id);
        const b = proposals.value.find(p => p.candidate_id === other);
        return !!(a && b && Math.min(a.end_us, b.end_us) > Math.max(a.start_us, b.start_us));
      })
    )
);

const isPartial = computed(() => {
  if (!props.analysis) return false;
  return (
    props.analysis.state !== 'completed' &&
    props.analysis.state !== 'running' &&
    props.analysis.completed_windows > 0 &&
    props.analysis.completed_windows < props.analysis.total_windows
  );
});
const remainingWindows = computed(() =>
  Math.max(0, (props.analysis?.total_windows || 0) - (props.analysis?.completed_windows || 0))
);

watch(
  () => props.analysis?.analysis_hash,
  (hash, old) => {
    if (hash !== old) {
      locallyEdited.value = false;
      loadDiscarded(hash);
      selected.value =
        hash && props.selection?.analysis_hash === hash ? [...props.selection.candidate_ids] : [];
      if (!proposals.value.some(p => p.candidate_id === focused.value)) focused.value = '';
      if (!props.analysis?.topic_groups.some(g => g.id === topic.value)) topic.value = '';
    }
  },
  { immediate: true }
);
watch(
  () => props.analysis?.job_id,
  (job, old) => {
    if (old && job !== old) {
      focused.value = '';
      topic.value = '';
      selected.value = [];
      discarded.value = [];
      locallyEdited.value = false;
    }
  }
);
watch(
  () => props.selection,
  value => {
    if (
      !locallyEdited.value &&
      value?.analysis_hash === props.analysis?.analysis_hash &&
      value?.analysis_hash
    )
      selected.value = [...value.candidate_ids];
  },
  { immediate: true }
);
watch(overlap, value => {
  if (value)
    notify.warning(
      'Seleção com trechos sobrepostos detectada. Os cortes não podem se sobrepor no vídeo original.'
    );
});
watch(current, value => {
  if (value && !value.eligible)
    notify.warning(value.reasons.join(' ') + ' A geração permanece bloqueada.', {
      key:
        'proposal:' +
        value.candidate_id +
        ':' +
        (props.analysis?.analysis_hash || props.analysis?.job_id),
    });
});

function toggle(p: Proposal) {
  if (!complete.value || !p.eligible || props.busy || discarded.value.includes(p.candidate_id))
    return;
  if (!selected.value.includes(p.candidate_id) && overlapsWithSelected(p)) {
    notify.warning(
      'Este trecho se sobrepõe a outro corte já selecionado. Desmarque o corte concorrente primeiro.'
    );
    return;
  }
  locallyEdited.value = true;
  selected.value = selected.value.includes(p.candidate_id)
    ? selected.value.filter(id => id !== p.candidate_id)
    : [...selected.value, p.candidate_id];
  emit('selection', {
    schema_version: '1.0',
    analysis_hash: props.analysis!.analysis_hash,
    candidate_ids: [...validSelection.value],
  });
}

function play(context = false) {
  if (!player.value || !current.value) return;
  player.value.currentTime = Math.max(0, current.value.start_us / 1e6 - (context ? 15 : 0));
  playEnd.value = current.value.end_us / 1e6 + (context ? 15 : 0);
  player.value.play().catch(() => {});
}
function stopAtEnd() {
  if (player.value && playEnd.value && player.value.currentTime >= playEnd.value) {
    player.value.pause();
    playEnd.value = 0;
  }
}
function choose(id: string) {
  focused.value = id;
  player.value?.pause();
  playEnd.value = 0;
}
</script>

<template>
  <section class="analysis-workspace">
    <!-- CABEÇALHO DO WORKSPACE DE CURADORIA -->
    <header class="analysis-heading" :class="{ 'is-complete': complete }">
      <div v-if="!complete" class="analysis-heading-text">
        <el-tag
          size="small"
          :type="
            analysis?.state === 'completed'
              ? 'success'
              : analysis?.state === 'failed'
                ? 'danger'
                : analysis?.state === 'partial'
                  ? 'warning'
                  : 'info'
          "
          effect="dark"
          class="status-pill"
          :data-status="analysis?.state"
        >
          {{ analysisStateLabel }}
        </el-tag>
        <p v-if="!analysis">A análise organizará os temas e os trechos da transcrição.</p>
      </div>
      <div v-else class="analysis-heading-meta">
        <span class="heading-stat-pill">
          <strong>{{ validSelection.length }}</strong> de
          <strong>{{ activeProposals.length }}</strong> propostas selecionadas
        </span>
      </div>

      <AppButton
        class="button primary generate-cta-btn"
        data-action="generate-selected"
        :disabled="!complete || !validSelection.length || busy || overlap"
        @click="
          emit('generate', {
            analysis_hash: analysis!.analysis_hash!,
            candidate_ids: [...validSelection],
          })
        "
      >
        <Scissors :size="16" />Gerar {{ validSelection.length }} prévia{{
          validSelection.length === 1 ? '' : 's'
        }}
        rápida{{ validSelection.length === 1 ? '' : 's' }}
      </AppButton>
    </header>

    <!-- BANNER DE RETOMADA COM 1 CLIQUE SE ANÁLISE FOR PARCIAL -->
    <p v-if="analysis?.diagnostic" role="alert" class="subtle">{{ analysis.diagnostic }}</p>
    <div v-else-if="isPartial" class="analysis-resume-card" role="status">
      <div class="resume-info">
        <strong
          >Análise parcial · {{ analysis?.completed_windows }} de
          {{ analysis?.total_windows }} janelas validadas</strong
        >
        <p>
          Faltam {{ remainingWindows }} janela{{ remainingWindows === 1 ? '' : 's' }} para concluir
          a análise completa. Você já pode consultar as propostas validadas ou continuar o
          processamento agora.
        </p>
        <small v-if="analysis?.state === 'failed' || analysis?.state === 'interrupted'"
          >Se a análise foi interrompida por limite de cota da IA (erro 429), aguarde alguns
          segundos antes de continuar.</small
        >
      </div>
      <AppButton
        class="button primary resume-analysis-btn"
        data-action="resume-analysis"
        :disabled="busy"
        @click="emit('resume')"
      >
        <RotateCcw :size="16" />Continuar análise das {{ remainingWindows }} janelas restantes
      </AppButton>
    </div>

    <div v-else-if="!complete" class="subtle partial-notice-bar" role="status">
      As propostas já validadas podem ser consultadas. A geração fica disponível quando a análise
      completa terminar.
    </div>

    <!-- WORKSPACE DESKTOP EM 3 COLUNAS REDIMENSIONÁVEIS COM EL-SPLITTER -->
    <el-splitter class="analysis-layout curation-3col-layout">
      <!-- COLUNA 1: NAVEGAÇÃO POR TEMAS -->
      <el-splitter-panel
        :size="240"
        :min="170"
        :max="380"
        class="curation-topics-col"
        role="region"
        aria-label="Temas identificados"
      >
        <div class="panel-inner-container">
          <div class="column-panel-header">
            <div class="panel-header-title">
              <h3>Temas</h3>
            </div>
            <span class="panel-counter-badge">{{
              visibleTopicGroups.length + (filterMode !== 'discarded' ? 1 : 0)
            }}</span>
          </div>

          <div class="topic-list custom-scrollbar" role="tablist" aria-label="Temas identificados">
            <AppButton
              v-if="filterMode !== 'discarded'"
              class="topic-chip-btn"
              :class="{ selected: !topic }"
              @click="
                topic = '';
                focused = '';
              "
            >
              <span class="chip-label">Todos os temas</span>
              <span class="chip-count">{{ activeProposals.length }}</span>
            </AppButton>
            <div
              v-for="group in visibleTopicGroups"
              :key="group.id"
              class="topic-chip-container"
              :class="{ selected: topic === group.id, discarded: isTopicDiscarded(group.id) }"
            >
              <AppButton
                class="topic-chip-btn"
                :class="{ selected: topic === group.id, discarded: isTopicDiscarded(group.id) }"
                @click="
                  topic = group.id;
                  focused = '';
                "
              >
                <span class="chip-label" :title="group.label">{{ group.label }}</span>
                <span class="chip-count">{{
                  activeProposals.filter(p => p.group_id === group.id).length
                }}</span>
              </AppButton>
              <button
                v-if="!isTopicDiscarded(group.id)"
                type="button"
                class="topic-action-icon-btn"
                title="Descartar tema e propostas"
                data-action="discard-topic"
                @click.stop="discardTopic(group.id)"
              >
                <Trash2 :size="12" />
              </button>
              <button
                v-else
                type="button"
                class="topic-action-icon-btn restore"
                title="Restaurar tema e propostas"
                data-action="restore-topic"
                @click.stop="restoreTopic(group.id)"
              >
                <RotateCcw :size="12" />
              </button>
            </div>
          </div>

          <div v-if="topic" class="topic-summary-box">
            <span class="summary-label">Resumo do tema:</span>
            <p
              v-for="summary in analysis?.topic_groups.find(g => g.id === topic)?.summaries"
              :key="summary"
            >
              {{ summary }}
            </p>
          </div>

          <!-- GAVETA COMPACTA DE DIAGNÓSTICO DO MOTOR -->
          <div class="topics-pipeline-drawer">
            <details class="analysis-explanation">
              <summary><Layers :size="13" /> Diagnóstico do motor</summary>
              <div class="explanation-inner-box">
                <AnalysisFeedback :jobs="jobs" />
              </div>
            </details>
          </div>
        </div>
      </el-splitter-panel>

      <!-- COLUNA 2: PROPOSTAS DE CORTES / WORK ITEMS -->
      <el-splitter-panel
        :size="380"
        :min="280"
        :max="550"
        class="curation-proposals-col"
        aria-label="Lista de propostas de cortes"
      >
        <div class="panel-inner-container">
          <div class="column-panel-header">
            <div class="panel-header-title">
              <h3>Propostas</h3>
            </div>
            <span class="panel-counter-badge">{{ filtered.length }} de {{ proposals.length }}</span>
          </div>

          <!-- BARRA DE CONTROLE DE SELEÇÃO E FILTROS -->
          <div class="proposals-control-bar">
            <div
              class="filter-mode-pills"
              role="tablist"
              aria-label="Filtro de status de propostas"
            >
              <button
                type="button"
                class="filter-pill-btn"
                :class="{ active: filterMode === 'active' }"
                @click="filterMode = 'active'"
              >
                Ativas ({{ activeProposals.length }})
              </button>
              <button
                v-if="discardedProposals.length > 0 || filterMode === 'discarded'"
                type="button"
                class="filter-pill-btn"
                :class="{ active: filterMode === 'discarded' }"
                @click="filterMode = 'discarded'"
              >
                Descartadas ({{ discardedProposals.length }})
              </button>
              <button
                type="button"
                class="filter-pill-btn"
                :class="{ active: filterMode === 'all' }"
                @click="filterMode = 'all'"
              >
                Todas ({{ proposals.length }})
              </button>
            </div>

            <div class="bulk-selection-actions" v-if="complete">
              <button
                type="button"
                class="bulk-action-btn"
                data-action="select-all-proposals"
                title="Selecionar todas as propostas elegíveis não descartadas"
                :disabled="busy || !activeProposals.length"
                @click="selectAllEligible"
              >
                <CheckCheck :size="12" /> Todas
              </button>
              <button
                v-if="selected.length > 0"
                type="button"
                class="bulk-action-btn"
                data-action="clear-selection"
                title="Limpar seleção atual"
                :disabled="busy"
                @click="clearSelection"
              >
                <X :size="12" /> Limpar
              </button>
            </div>
          </div>

          <label class="search-proposals-wrap">
            <Search :size="15" />
            <input
              v-model="search"
              type="search"
              placeholder="Filtrar por palavra..."
              aria-label="Buscar nas propostas"
            />
          </label>

          <div
            class="proposal-list custom-scrollbar"
            tabindex="0"
            role="region"
            aria-label="Propostas de cortes"
          >
            <article
              v-for="p in filtered"
              :key="p.candidate_id"
              class="proposal-card"
              :class="{
                selected: current?.candidate_id === p.candidate_id,
                overlapping: overlapsWithSelected(p),
                checked: selected.includes(p.candidate_id),
                discarded: discarded.includes(p.candidate_id),
              }"
              tabindex="0"
              role="button"
              :aria-pressed="selected.includes(p.candidate_id)"
              :aria-label="'Proposta: ' + p.title + ' (' + time(p.duration_us) + ')'"
              @click="choose(p.candidate_id)"
              @keydown.enter.prevent="choose(p.candidate_id)"
              @keydown.space.prevent="choose(p.candidate_id)"
            >
              <div class="proposal-top-row">
                <label
                  class="proposal-checkbox-label"
                  :title="
                    discarded.includes(p.candidate_id)
                      ? 'Restaure a proposta para selecioná-la'
                      : overlapsWithSelected(p)
                        ? 'Sobrepõe um corte já selecionado'
                        : undefined
                  "
                  @click.stop
                >
                  <input
                    type="checkbox"
                    :checked="selected.includes(p.candidate_id)"
                    :disabled="
                      !complete ||
                      !p.eligible ||
                      busy ||
                      discarded.includes(p.candidate_id) ||
                      overlapsWithSelected(p)
                    "
                    :aria-label="'Selecionar ' + p.title"
                    @change="toggle(p)"
                  />
                </label>
                <div class="proposal-open" @click="choose(p.candidate_id)">
                  <strong>{{ p.title }}</strong>
                  <div class="proposal-time-subline">
                    <span class="time-range"
                      ><Clock :size="11" /> {{ time(p.start_us) }} · {{ time(p.duration_us) }}</span
                    >
                    <span
                      v-if="overlapsWithSelected(p)"
                      class="status-pill conflict-pill"
                      data-status="warning"
                      title="Este trecho se sobrepõe a outro corte já selecionado"
                    >
                      <AlertTriangle :size="11" /> Sobrepõe seleção
                    </span>
                    <span
                      v-else-if="discarded.includes(p.candidate_id)"
                      class="status-pill discarded-pill"
                    >
                      <Trash2 :size="11" /> Descartada
                    </span>
                  </div>
                </div>
                <button
                  type="button"
                  v-if="!discarded.includes(p.candidate_id)"
                  class="proposal-discard-icon-btn"
                  title="Descartar esta proposta"
                  data-action="discard-proposal"
                  @click.stop="discard(p.candidate_id)"
                >
                  <Trash2 :size="13" />
                </button>
                <button
                  type="button"
                  v-else
                  class="proposal-restore-icon-btn"
                  title="Restaurar esta proposta"
                  data-action="restore-proposal"
                  @click.stop="restore(p.candidate_id)"
                >
                  <RotateCcw :size="12" /> Restaurar
                </button>
              </div>
            </article>

            <p v-if="!filtered.length" class="subtle empty-proposals">
              {{
                proposals.length
                  ? 'Nenhuma proposta corresponde ao filtro.'
                  : 'Aguardando propostas validadas.'
              }}
            </p>
          </div>
        </div>
      </el-splitter-panel>

      <!-- COLUNA 3: SUÍTE DE INSPEÇÃO EDITORIAL -->
      <el-splitter-panel :min="380" class="curation-inspection-col">
        <div class="panel-inner-container">
          <section v-if="current" class="proposal-detail custom-scrollbar">
            <div class="inspection-head-bar">
              <div class="inspection-step-wrap">
                <span class="inspection-title-step">Inspeção Editorial</span>
              </div>
              <div class="inspection-time-badge">
                <Clock :size="13" />
                <span
                  >{{ time(current.start_us) }} – {{ time(current.end_us) }} ({{
                    time(current.duration_us)
                  }})</span
                >
              </div>
            </div>

            <h3 class="inspection-current-title">{{ current.title }}</h3>

            <!-- MINI PLAYER COMPACTO DE APOIO (ÁUDIO/VÍDEO) -->
            <div class="compact-media-bar">
              <div class="mini-video-frame">
                <video
                  v-if="sourceUrl"
                  v-recover-media="sourceUrl"
                  ref="player"
                  :src="sourceUrl"
                  preload="metadata"
                  playsinline
                  @timeupdate="stopAtEnd"
                ></video>
                <div v-else class="media-placeholder">
                  <Volume2 :size="24" />
                </div>
              </div>
              <div class="media-controls-wrap">
                <div class="media-status-row">
                  <span class="media-type-badge"><Volume2 :size="13" /> Trecho original</span>
                  <span class="media-timecode"
                    >{{ time(current.start_us) }} → {{ time(current.end_us) }}</span
                  >
                </div>
                <div class="proposal-play">
                  <AppButton
                    class="button small primary play-btn"
                    :disabled="!sourceUrl"
                    @click="play()"
                  >
                    <AppIcon name="play" size="sm" /> Ouvir trecho
                  </AppButton>
                  <AppButton
                    class="button small secondary context-btn"
                    :disabled="!sourceUrl"
                    @click="play(true)"
                  >
                    Contexto (+15s)
                  </AppButton>
                </div>
              </div>
            </div>

            <!-- GANCHO SOCIAL (PRIMEIROS 7 SEGUNDOS) -->
            <div class="opening-copy editorial-section-block">
              <span class="editorial-section-label">Frase de abertura · primeiros 7 segundos</span>
              <p class="hook-text">
                "{{
                  current.opening_text ||
                  'A próxima análise poderá sugerir uma frase curta para este trecho.'
                }}"
              </p>
            </div>

            <!-- RACIOCÍNIO EDITORIAL -->
            <div class="inspection-block rationale-card editorial-section-block">
              <span class="editorial-section-label">Justificativa editorial</span>
              <p class="proposal-rationale">{{ current.rationale }}</p>
              <div class="editorial-flags">
                <span
                  v-for="(label, key) in {
                    completeness: 'Raciocínio completo',
                    standalone_context: 'Contexto suficiente',
                    qualification_preserved: 'Ressalvas preservadas',
                  }"
                  :key="key"
                  class="editorial-flag-item"
                >
                  {{ label }}:
                  <b>{{
                    current.editorial[key] === 'yes'
                      ? 'Sim'
                      : current.editorial[key] === 'no'
                        ? 'Não'
                        : 'Incerto'
                  }}</b>
                </span>
              </div>
            </div>

            <div v-if="!current.eligible" class="restriction-box">
              <AppButton
                class="text-button"
                @click="
                  notify.warning(current.reasons.join(' ') + ' A geração permanece bloqueada.')
                "
              >
                <AlertTriangle :size="14" /> Ver motivo da restrição
              </AppButton>
              <p v-for="warning in current.warnings" :key="warning" class="subtle">{{ warning }}</p>
            </div>

            <!-- TRANSCRIÇÃO COMPLETA E CONTEXTO -->
            <details class="proposal-transcript" open>
              <summary><FileText :size="14" /> Fala e contexto original</summary>
              <div class="transcript-preview-body">
                <p v-if="current.context_before" class="context-text before">
                  {{ current.context_before }}
                </p>
                <p class="core-text">{{ current.text }}</p>
                <p v-if="current.context_after" class="context-text after">
                  {{ current.context_after }}
                </p>
              </div>
            </details>
            <small class="evidence-subtext"
              >{{ current.evidence_word_ids.length }} referência(s) à transcrição original ·
              Timestamps estimados pelo ASR</small
            >

            <!-- AÇÃO PRINCIPAL DE SELEÇÃO E DESCARTE PARA O CORTE FOCADO -->
            <div class="inspection-footer-actions">
              <div class="inspection-actions-row">
                <AppButton
                  class="button primary select-focused-btn"
                  data-action="select-focused"
                  :disabled="
                    !complete ||
                    !current.eligible ||
                    busy ||
                    discarded.includes(current.candidate_id) ||
                    (!selected.includes(current.candidate_id) && overlapsWithSelected(current))
                  "
                  :title="
                    discarded.includes(current.candidate_id)
                      ? 'Restaure a proposta para selecioná-la'
                      : !selected.includes(current.candidate_id) && overlapsWithSelected(current)
                        ? 'Sobrepõe um corte já selecionado'
                        : undefined
                  "
                  @click="toggle(current)"
                >
                  <Check v-if="selected.includes(current.candidate_id)" :size="16" />
                  {{
                    selected.includes(current.candidate_id)
                      ? 'Remover da seleção'
                      : 'Selecionar este trecho'
                  }}
                </AppButton>

                <AppButton
                  v-if="!discarded.includes(current.candidate_id)"
                  class="button secondary discard-focused-btn"
                  data-action="discard-focused"
                  :disabled="busy"
                  title="Descartar esta proposta"
                  @click="discard(current.candidate_id)"
                >
                  <Trash2 :size="14" /> Descartar proposta
                </AppButton>
                <AppButton
                  v-else
                  class="button secondary restore-focused-btn"
                  data-action="restore-focused"
                  :disabled="busy"
                  title="Restaurar esta proposta"
                  @click="restore(current.candidate_id)"
                >
                  <RotateCcw :size="14" /> Restaurar proposta
                </AppButton>
              </div>

              <p v-if="discarded.includes(current.candidate_id)" class="subtle discard-notice">
                Esta proposta está marcada como descartada. Você pode restaurá-la para voltar a
                selecioná-la.
              </p>
              <p
                v-else-if="
                  !selected.includes(current.candidate_id) && overlapsWithSelected(current)
                "
                class="subtle overlap-notice"
              >
                Este trecho se sobrepõe a um corte já selecionado. Desmarque o corte concorrente
                para poder selecioná-lo.
              </p>
            </div>
          </section>

          <section v-else class="proposal-detail proposal-empty" aria-label="Inspeção do trecho">
            <el-empty
              :description="
                proposals.length ? 'Escolha uma proposta' : 'Os trechos aparecerão aqui'
              "
            >
              <template #image>
                <FileText :size="40" />
              </template>
              <template #default>
                <h3>
                  {{ proposals.length ? 'Escolha uma proposta' : 'Os trechos aparecerão aqui' }}
                </h3>
                <p>
                  {{
                    proposals.length
                      ? 'Confira o conteúdo original, a justificativa e a integridade antes de selecionar.'
                      : 'Quando houver propostas validadas, você poderá ouvir o contexto e escolher os cortes nesta área.'
                  }}
                </p>
              </template>
            </el-empty>
          </section>
        </div>
      </el-splitter-panel>
    </el-splitter>

    <!-- RODAPÉ INTEGRADO DOCK (NUNCA FLUTUA SOBRE CONTEÚDO) -->
    <footer class="curation-dock-bar" v-if="complete && proposals.length > 0">
      <div class="dock-selection-info">
        <span class="dock-count-pill">{{ validSelection.length }}</span>
        <div class="dock-text">
          <strong
            >{{ validSelection.length }} corte{{
              validSelection.length === 1 ? '' : 's'
            }}
            selecionado{{ validSelection.length === 1 ? '' : 's' }}</strong
          >
          <small v-if="validSelection.length"
            >Duração total estimada: ~{{ time(totalSelectedDurationUs) }}</small
          >
          <small v-else>Selecione os melhores trechos para gerar vídeos 9:16 verticais</small>
        </div>
      </div>

      <AppButton
        class="button primary generate-dock-btn"
        data-action="generate-selected-dock"
        :disabled="!complete || !validSelection.length || busy || overlap"
        @click="
          emit('generate', {
            analysis_hash: analysis!.analysis_hash!,
            candidate_ids: [...validSelection],
          })
        "
      >
        <Scissors :size="16" />Gerar {{ validSelection.length }} prévia{{
          validSelection.length === 1 ? '' : 's'
        }}
        rápida{{ validSelection.length === 1 ? '' : 's' }}
        {{ validSelection.length === 1 ? 'vertical' : 'verticais' }}
      </AppButton>
    </footer>
  </section>
</template>

<style scoped>
.analysis-workspace {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  flex: 1;
  min-height: 0;
  min-width: 0;
  box-sizing: border-box;
}

.analysis-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  min-height: 38px;
  flex-shrink: 0;
}

.analysis-heading.is-complete {
  margin-bottom: 2px;
}

.heading-stat-pill {
  font-size: 0.82rem;
  color: var(--color-text-secondary, var(--muted));
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  padding: 5px 12px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.heading-stat-pill strong {
  color: var(--color-text-primary, var(--ink));
  font-weight: 600;
}

.analysis-heading-text h2 {
  margin: 2px 0 4px;
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--color-text-primary, var(--ink));
}

.analysis-heading-text p {
  margin: 0;
  font-size: 0.82rem;
  color: var(--color-text-muted, var(--muted));
}

.generate-cta-btn {
  font-weight: 600;
  padding: 8px 16px;
}

/* 3-COLUMN WORKSPACE SPLITTER */
.analysis-layout.curation-3col-layout {
  flex: 1;
  height: auto;
  min-height: 0;
  min-width: 0;
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: var(--radius-panel, 12px);
  overflow: hidden;
  box-sizing: border-box;
}

:deep(.el-splitter) {
  height: 100%;
  width: 100%;
}

:deep(.el-splitter__bar) {
  background: var(--color-border-subtle, var(--line));
  width: 1px !important;
  transition:
    background 0.15s ease,
    width 0.15s ease;
}

:deep(.el-splitter__bar:hover) {
  background: var(--color-action-primary);
  width: 3px !important;
}

.panel-inner-container {
  height: 100%;
  min-height: 0;
  width: 100%;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow: hidden;
  box-sizing: border-box;
}

/* FLAT MINIMALIST COLUMNS INSIDE SPLITTER */
.curation-topics-col,
.curation-proposals-col,
.curation-inspection-col {
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  height: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.curation-topics-col .topic-list {
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  padding: 0 !important;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.column-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border-subtle, var(--line));
  flex-shrink: 0;
}

.panel-header-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-header-title h3 {
  font-size: 0.92rem;
  font-weight: 700;
  margin: 0;
  color: var(--color-text-primary, var(--ink));
}

.selection-step-badge {
  font-family: var(--font-mono, monospace);
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  background: var(--color-surface-selected);
  color: var(--color-text-primary);
  padding: 1px 6px;
  border-radius: 4px;
  border: 1px solid var(--color-border-subtle);
  display: inline-flex;
  align-items: center;
}

.panel-counter-badge {
  font-family: var(--font-mono, monospace);
  font-size: 0.72rem;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.05);
  color: var(--color-text-muted, #a0abba);
  padding: 1px 8px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  display: inline-flex;
  align-items: center;
}

.topic-chip-container {
  display: flex;
  align-items: center;
  position: relative;
  width: 100%;
  border-radius: 8px;
  transition: all 0.15s ease;
  gap: 2px;
}

.topic-chip-container .topic-chip-btn {
  flex: 1;
  min-width: 0;
}

.topic-chip-container:hover .topic-action-icon-btn,
.topic-action-icon-btn:focus-visible {
  opacity: 1;
  visibility: visible;
}

.topic-chip-container.discarded {
  opacity: 0.55;
}

.topic-action-icon-btn {
  position: static;
  background: transparent;
  border: none;
  color: var(--color-text-muted, var(--muted));
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  visibility: hidden;
  flex-shrink: 0;
  margin-right: 4px;
  transition: all 0.15s ease;
}

.topic-action-icon-btn:hover {
  color: var(--color-danger, #ef4444);
  background: rgba(239, 68, 68, 0.12);
}

.topic-action-icon-btn.restore {
  opacity: 1;
  visibility: visible;
}

.topic-action-icon-btn.restore:hover {
  color: var(--color-success, #10b981);
  background: rgba(16, 185, 129, 0.12);
}

.topic-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
  flex: 1;
  padding-right: 2px;
}

.topic-chip-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  text-align: left;
  padding: 8px 10px;
  border-radius: 8px;
  font-size: 0.8rem;
  background: transparent;
  border: 1px solid transparent;
  color: var(--color-text-secondary, var(--muted));
  transition: all 0.15s ease;
  cursor: pointer;
}

.topic-chip-btn:hover {
  background: var(--color-surface-hover, var(--soft));
  color: var(--color-text-primary, var(--ink));
}

.topic-chip-btn.selected {
  background: var(--color-surface-selected);
  border-color: var(--color-border-strong);
  color: var(--color-text-primary);
  font-weight: 600;
}

.chip-label {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: normal;
  line-height: 1.3;
  word-break: break-word;
}

.chip-count {
  font-size: 0.72rem;
  opacity: 0.85;
  background: var(--color-surface-raised, rgba(255, 255, 255, 0.06));
  padding: 1px 6px;
  border-radius: 4px;
  margin-left: 6px;
  flex-shrink: 0;
}

.topic-summary-box {
  background: transparent;
  border-left: 2px solid var(--color-border-strong);
  padding: 4px 10px;
  font-size: 0.78rem;
  line-height: 1.4;
  color: var(--color-text-secondary, var(--muted));
  max-height: 120px;
  overflow-y: auto;
}

.summary-label {
  display: block;
  font-weight: 600;
  color: var(--color-text-primary, var(--ink));
  margin-bottom: 3px;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.topic-summary-box p {
  margin: 0;
}

.topics-pipeline-drawer {
  margin-top: auto;
  border-top: 1px solid var(--color-border-subtle, var(--line));
  padding-top: 8px;
}

.topics-pipeline-drawer details summary {
  font-size: 0.75rem;
  color: var(--color-text-muted, var(--muted));
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 6px;
  border-radius: 6px;
}

.topics-pipeline-drawer details summary:hover {
  background: var(--color-surface-hover, var(--soft));
  color: var(--color-text-primary, var(--ink));
}

.explanation-inner-box {
  margin-top: 6px;
  max-height: 120px;
  overflow-y: auto;
  font-size: 0.75rem;
}

/* COLUMN 2: PROPOSALS */
.curation-proposals-col {
  height: 100%;
  overflow: hidden;
  box-sizing: border-box;
}

.curation-proposals-col .proposal-list {
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  padding: 0 4px 0 0 !important;
  flex: 1;
  min-height: 120px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.proposals-control-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-shrink: 0;
}

.filter-mode-pills {
  display: inline-flex;
  gap: 2px;
  background: var(--color-canvas);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-control, 6px);
  padding: 2px;
  flex-shrink: 0;
}

.filter-pill-btn {
  background: transparent;
  border: 1px solid transparent;
  border-radius: 4px;
  padding: 3px 8px;
  font-size: 0.72rem;
  color: var(--color-text-muted, var(--muted));
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.filter-pill-btn:hover {
  color: var(--color-text-primary, var(--ink));
}

.filter-pill-btn.active {
  background: var(--color-surface-raised);
  color: var(--color-text-primary);
  border-color: var(--color-border-subtle);
  font-weight: 600;
}

.bulk-selection-actions {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.bulk-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: var(--color-surface-raised, rgba(255, 255, 255, 0.04));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: 6px;
  padding: 3px 8px;
  font-size: 0.72rem;
  color: var(--color-text-secondary, var(--muted));
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.bulk-action-btn:hover:not(:disabled) {
  background: var(--color-surface-hover, var(--soft));
  color: var(--color-text-primary, var(--ink));
  border-color: var(--color-border-strong);
}

.bulk-action-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.search-proposals-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--color-canvas);
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: var(--radius-control, 6px);
  padding: 6px 10px;
  color: var(--color-text-muted, var(--muted));
  flex-shrink: 0;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

.search-proposals-wrap:focus-within {
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 1px var(--color-border-focus);
}

.search-proposals-wrap input {
  border: none;
  background: transparent;
  color: var(--color-text-primary, var(--ink));
  font-size: 0.8rem;
  width: 100%;
  outline: none;
}

.proposal-card {
  background: var(--color-surface-raised, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: var(--radius-control, 6px);
  padding: 9px 12px;
  transition: all 0.15s ease;
  cursor: pointer;
  outline: none;
  box-sizing: border-box;
}

.proposal-card:hover {
  border-color: var(--color-border-strong);
  background: var(--color-surface-hover);
}

.proposal-card:focus-visible {
  border-color: var(--color-border-strong);
  box-shadow: 0 0 0 2px var(--color-border-focus);
}

.proposal-card.selected {
  border-color: var(--color-border-strong);
  background: var(--color-surface-selected);
}

.proposal-card.checked {
  box-shadow: inset 3px 0 0 var(--color-action-primary, #eceef0);
}

.proposal-card.selected.checked {
  box-shadow: inset 3px 0 0 var(--color-action-primary, #eceef0);
}

.proposal-card.overlapping {
  opacity: 0.82;
}

.proposal-card.discarded {
  opacity: 0.62;
  border-style: dashed;
}

.proposal-card.discarded:hover {
  opacity: 0.88;
}

.proposal-top-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.proposal-checkbox-label {
  display: inline-flex;
  align-items: center;
  padding-top: 1px;
  cursor: pointer;
  flex-shrink: 0;
}

.proposal-checkbox-label input {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--color-action-primary, #e5e7eb);
}

.proposal-discard-icon-btn,
.proposal-restore-icon-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 3px 6px;
  border-radius: 5px;
  color: var(--color-text-muted, var(--muted));
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.7rem;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.proposal-discard-icon-btn:hover {
  color: var(--color-danger, #ef4444);
  background: rgba(239, 68, 68, 0.12);
}

.proposal-restore-icon-btn {
  color: var(--color-success, #10b981);
  background: rgba(16, 185, 129, 0.1);
  padding: 2px 7px;
}

.proposal-restore-icon-btn:hover {
  background: rgba(16, 185, 129, 0.2);
}

.proposal-open {
  flex: 1;
  min-width: 0;
  background: transparent;
  border: none;
  padding: 0;
  text-align: left;
  cursor: pointer;
  color: inherit;
}

.proposal-open strong {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 0.85rem;
  font-weight: 600;
  line-height: 1.3;
  color: var(--color-text-primary, var(--ink));
  margin-bottom: 4px;
}

.proposal-time-subline {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.time-range {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.72rem;
  color: var(--color-text-muted, var(--muted));
  font-family: var(--font-mono, monospace);
}

.duration-pill {
  font-size: 0.68rem;
  background: var(--color-surface-hover, var(--soft));
  color: var(--color-text-muted, var(--muted));
  padding: 1px 5px;
  border-radius: 4px;
  font-weight: 600;
}

.conflict-pill {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.12);
  border-color: rgba(245, 158, 11, 0.3);
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.discarded-pill {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.25);
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* COLUMN 3: INSPECTION SUITE */
.curation-inspection-col {
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.curation-inspection-col .proposal-detail {
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  padding: 16px 20px 0 20px;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 14px;
  position: relative;
}

.inspection-head-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.inspection-step-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.inspection-title-step {
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-muted, var(--muted));
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
  font-family: var(--font-mono, monospace);
}

.inspection-current-title {
  font-size: 1.15rem;
  font-weight: 700;
  line-height: 1.35;
  margin: 0;
  color: var(--color-text-primary, var(--ink));
  flex-shrink: 0;
}

/* COMPACT MEDIA BAR */
.compact-media-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--color-surface-hover, rgba(255, 255, 255, 0.03));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: 8px;
  padding: 10px 12px;
  flex-shrink: 0;
}

.mini-video-frame {
  width: 140px;
  height: 79px;
  aspect-ratio: 16/9;
  border-radius: 6px;
  overflow: hidden;
  background: #000;
  flex-shrink: 0;
  border: 1px solid var(--color-border-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
}

.mini-video-frame video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.media-placeholder {
  color: var(--color-text-muted, var(--muted));
  opacity: 0.6;
}

.media-controls-wrap {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.media-status-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.media-type-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-muted, var(--muted));
}

.media-timecode {
  font-family: var(--font-mono, monospace);
  font-size: 0.76rem;
  color: var(--color-text-primary);
  font-weight: 600;
}

.proposal-play {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.proposal-play .play-btn {
  font-weight: 600;
  white-space: nowrap;
}

.proposal-play .context-btn {
  white-space: nowrap;
}

/* SOCIAL OPENING HOOK - EDITORIAL PULL-QUOTE */
/* EDITORIAL SECTION BLOCK */
.editorial-section-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 0;
  border-bottom: 1px solid var(--color-border-subtle, rgba(255, 255, 255, 0.06));
}

.editorial-section-label {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-text-muted, var(--muted));
}

.hook-text {
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--color-text-primary, var(--ink));
  line-height: 1.45;
  margin: 0;
  font-style: italic;
  padding-left: 10px;
  border-left: 2px solid var(--color-border-strong);
}

/* RATIONALE SECTION - FLAT EDITORIAL */
.rationale-card {
  background: transparent;
  border: none;
  border-radius: 0;
  padding: 10px 0;
}

.block-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: var(--color-text-primary);
  margin-bottom: 6px;
}

.proposal-rationale {
  font-size: 0.82rem;
  line-height: 1.4;
  margin: 0 0 10px;
  color: var(--color-text-secondary, var(--muted));
}

.editorial-flags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.editorial-flag-item {
  font-size: 0.75rem;
  background: transparent;
  border: none;
  padding: 0;
  color: var(--color-text-muted, var(--muted));
}

.editorial-flag-item b {
  color: var(--color-text-primary, var(--ink));
}

.restriction-box {
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.25);
  border-radius: 8px;
  padding: 10px 12px;
}

.proposal-transcript {
  background: transparent;
  border: none;
  border-top: 1px solid var(--color-border-subtle, var(--line));
  border-radius: 0;
  padding: 10px 0;
}

.proposal-transcript summary {
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--color-text-primary, var(--ink));
}

.transcript-preview-body {
  margin-top: 8px;
  font-size: 0.8rem;
  line-height: 1.4;
}

.context-text {
  color: var(--color-text-muted, var(--muted));
  font-style: italic;
  margin: 4px 0;
}

.core-text {
  font-weight: 500;
  color: var(--color-text-primary, var(--ink));
  margin: 6px 0;
}

.evidence-subtext {
  font-size: 0.72rem;
  color: var(--color-text-muted, var(--muted));
}

.inspection-footer-actions {
  position: sticky;
  bottom: 0;
  margin-top: auto;
  margin-left: -20px;
  margin-right: -20px;
  padding: 12px 20px 14px;
  background: var(--color-surface, var(--panel));
  border-top: 1px solid var(--color-border-subtle, var(--line));
  box-shadow: 0 -6px 16px rgba(0, 0, 0, 0.4);
  z-index: 5;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.inspection-actions-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.select-focused-btn {
  min-height: 38px;
  font-size: 0.88rem;
  font-weight: 600;
  flex: 1;
}

.discard-focused-btn {
  color: var(--color-danger, #ef4444);
  border-color: rgba(239, 68, 68, 0.3);
}

.discard-focused-btn:hover {
  background: rgba(239, 68, 68, 0.1) !important;
  border-color: var(--color-danger, #ef4444) !important;
}

.restore-focused-btn {
  color: var(--color-success, #10b981);
  border-color: rgba(16, 185, 129, 0.3);
}

.restore-focused-btn:hover {
  background: rgba(16, 185, 129, 0.1) !important;
  border-color: var(--color-success, #10b981) !important;
}

.discard-notice {
  color: #f87171;
  font-size: 0.76rem;
  margin: 0;
  line-height: 1.35;
}

.proposal-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px 20px;
  gap: 12px;
  color: var(--color-text-muted, var(--muted));
}

.proposal-empty h3 {
  font-size: 1.1rem;
  margin: 0;
  color: var(--color-text-primary, var(--ink));
}

.proposal-empty p {
  max-width: 320px;
  font-size: 0.82rem;
  line-height: 1.4;
  margin: 0;
}

/* RODAPÉ DOCK INTEGRADO */
.curation-dock-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-top: 1px solid var(--color-border-strong);
  border-radius: var(--radius-control, 8px);
  padding: 8px 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  flex-shrink: 0;
}

.dock-selection-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dock-count-pill {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--color-action-primary);
  color: var(--color-action-primary-text);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.78rem;
}

.dock-text strong {
  font-size: 0.85rem;
  display: block;
  color: var(--color-text-primary, var(--ink));
}

.dock-text small {
  font-size: 0.74rem;
  color: var(--color-text-muted, var(--muted));
}

.generate-dock-btn {
  font-size: 0.82rem;
  font-weight: 600;
  padding: 6px 14px;
}

.analysis-resume-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-left: 4px solid var(--color-border-strong);
  border-radius: 10px;
  padding: 12px 16px;
}

.resume-info strong {
  display: block;
  font-size: 0.92rem;
  margin-bottom: 2px;
}

.resume-info p {
  margin: 0 0 2px;
  font-size: 0.82rem;
  color: var(--color-text-muted, var(--muted));
}

.resume-info small {
  display: block;
  font-size: 0.75rem;
  color: var(--color-warning-text, #f59e0b);
}

.resume-analysis-btn {
  white-space: nowrap;
  flex-shrink: 0;
}

.overlap-notice {
  margin-top: 4px;
  color: var(--color-warning-text, #f59e0b);
  font-size: 0.8rem;
  font-weight: 500;
}

@media (max-width: 1100px) {
  .curation-3col-layout {
    grid-template-columns: 190px 330px minmax(0, 1fr);
    gap: 10px;
  }
}

@media (max-width: 900px) {
  .analysis-layout.curation-3col-layout {
    overflow-x: auto;
    overscroll-behavior-inline: contain;
  }
}
</style>
