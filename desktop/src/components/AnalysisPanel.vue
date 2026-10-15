<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import AppButton from './AppButton.vue';
import TopicNavigation from './analysis/TopicNavigation.vue';
import ProposalList from './analysis/ProposalList.vue';
import ProposalInspectorDrawer from './analysis/ProposalInspectorDrawer.vue';
import SelectionDock from './analysis/SelectionDock.vue';
import TechnicalDetails from './ui/TechnicalDetails.vue';
import { useProposalSelection } from '../composables/useProposalSelection';
import type { AnalysisView, AnalysisSelection, Job, Proposal } from '../types';
import { analysisLabels } from '../format';
import { notify } from '../notifications';
import AnalysisFeedback from './AnalysisFeedback.vue';
import { useDiscardedProposals } from '../composables/useDiscardedProposals';

const props = defineProps<{
  analysis: AnalysisView | null;
  selection: AnalysisSelection | null;
  jobs: Job[];
  sourceUrl: string;
  busy: boolean;
  loadSource?: () => Promise<string>;
}>();
const emit = defineEmits<{
  generate: [value: { analysis_hash: string; candidate_ids: string[] }];
  selection: [value: AnalysisSelection];
  resume: [];
}>();
const topic = ref(''),
  search = ref(''),
  focused = ref(''),
  drawerOpen = ref(false);
const workspace = ref<HTMLElement>();
function restoreInspectionFocus() {
  const target = workspace.value?.querySelector<HTMLElement>('.proposal-open, .proposal-items');
  target?.focus();
}
const locallyEdited = ref(false);
const { discarded, loadDiscarded, discardItem, restoreItem, discardMany, restoreMany } =
  useDiscardedProposals();
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
    return all.filter(g =>
      proposals.value.some(p => p.group_id === g.id && discarded.value.includes(p.candidate_id))
    );
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

const current = computed(() => proposals.value.find(p => p.candidate_id === focused.value));
const {
  selected,
  validSelection,
  hasOverlapWithSelected: overlapsWithSelected,
  toggle: toggleSelection,
  selectAllEligible: selectEligible,
} = useProposalSelection(proposals, discarded);
const topicCounts = computed(() =>
  Object.fromEntries(
    (props.analysis?.topic_groups || []).map(g => [
      g.id,
      proposals.value.filter(
        p =>
          p.group_id === g.id &&
          (filterMode.value === 'all' ||
            discarded.value.includes(p.candidate_id) === (filterMode.value === 'discarded'))
      ).length,
    ])
  )
);
const discardedTopicIds = computed(() =>
  (props.analysis?.topic_groups || []).filter(g => isTopicDiscarded(g.id)).map(g => g.id)
);
const overlappingIds = computed(() =>
  proposals.value.filter(overlapsWithSelected).map(p => p.candidate_id)
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
  const candidates = proposals.value.filter(
    p =>
      p.eligible &&
      !discarded.value.includes(p.candidate_id) &&
      (!topic.value || p.group_id === topic.value)
  );
  const toSelect = selectEligible(topic.value);
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
      if (old) drawerOpen.value = false;
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
    if (old && job && job !== old && !props.analysis?.analysis_hash) {
      drawerOpen.value = false;
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
  toggleSelection(p.candidate_id);
  emit('selection', {
    schema_version: '1.0',
    analysis_hash: props.analysis!.analysis_hash,
    candidate_ids: [...validSelection.value],
  });
}

function choose(id: string) {
  focused.value = id;
  drawerOpen.value = true;
}
function chooseTopic(id: string) {
  topic.value = id;
}
watch(current, value => {
  if (!value) drawerOpen.value = false;
});
</script>

<template>
  <section ref="workspace" class="analysis-workspace editorial-analysis">
    <header class="analysis-heading">
      <h2>Análise editorial</h2>
      <span>{{
        complete ? activeProposals.length + ' propostas ativas' : analysisStateLabel
      }}</span>
    </header>
    <p v-if="analysis?.diagnostic" role="alert">{{ analysis.diagnostic }}</p>
    <div v-else-if="isPartial" class="analysis-resume-card" role="status">
      <div>
        <strong
          >Análise parcial · {{ analysis?.completed_windows }} de
          {{ analysis?.total_windows }} janelas validadas</strong
        >
        <p>
          Faltam {{ remainingWindows }} janelas para concluir. Você já pode consultar as propostas
          validadas.
        </p>
      </div>
      <AppButton
        class="button secondary"
        data-action="resume-analysis"
        :disabled="busy"
        @click="emit('resume')"
        >Continuar análise</AppButton
      >
    </div>
    <p v-else-if="!complete" role="status" class="subtle">
      A geração de prévias fica disponível quando a análise completa terminar.
    </p>
    <div class="editorial-regions">
      <TopicNavigation
        :topics="visibleTopicGroups"
        :selected-topic-id="topic"
        :proposal-counts="topicCounts"
        :discarded-topic-ids="discardedTopicIds"
        :total="
          filterMode === 'active'
            ? activeProposals.length
            : filterMode === 'discarded'
              ? discardedProposals.length
              : proposals.length
        "
        :busy="busy"
        @select-topic="chooseTopic"
        @discard-topic="discardTopic"
        @restore-topic="restoreTopic"
      />
      <ProposalList
        v-model:search="search"
        v-model:filter-mode="filterMode"
        :proposals="filtered"
        :selected-ids="selected"
        :discarded-ids="discarded"
        :overlapping-ids="overlappingIds"
        :focused-id="focused"
        :busy="busy"
        :analysis-complete="complete"
        :counts="{
          active: activeProposals.length,
          discarded: discardedProposals.length,
          all: proposals.length,
        }"
        @focus-proposal="choose"
        @toggle-selection="toggle"
        @discard-proposal="discard"
        @restore-proposal="restore"
        @select-eligible="selectAllEligible"
        @clear-selection="clearSelection"
      />
    </div>
    <TechnicalDetails title="Diagnóstico do motor"
      ><AnalysisFeedback :jobs="jobs"
    /></TechnicalDetails>
    <SelectionDock
      :count="validSelection.length"
      :duration-us="totalSelectedDurationUs"
      :conflict="overlap"
      :disabled="!complete || !validSelection.length || busy || overlap"
      @generate="
        complete &&
        !busy &&
        !overlap &&
        validSelection.length &&
        emit('generate', {
          analysis_hash: analysis!.analysis_hash!,
          candidate_ids: [...validSelection],
        })
      "
    />
    <ProposalInspectorDrawer
      v-model="drawerOpen"
      :proposal="current"
      :source-url="sourceUrl"
      :load-source="loadSource"
      :selected="!!current && selected.includes(current.candidate_id)"
      :discarded="!!current && discarded.includes(current.candidate_id)"
      :overlapping="!!current && overlapsWithSelected(current)"
      :busy="busy"
      :analysis-complete="complete"
      @restore-focus="restoreInspectionFocus"
      @toggle-selection="current && toggle(current)"
      @discard="current && discard(current.candidate_id)"
      @restore="current && restore(current.candidate_id)"
    />
  </section>
</template>
<style scoped>
.editorial-analysis {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  height: 100%;
  min-width: 0;
  min-height: 0;
}
.analysis-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 16px;
  flex-shrink: 0;
}
.analysis-heading h2 {
  font-size: var(--font-size-region);
}
.analysis-heading span {
  font-size: var(--font-size-control);
  color: var(--color-text-secondary);
}
.editorial-regions {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 24px;
  flex: 1;
  min-height: 180px;
  min-width: 0;
  overflow: hidden;
}
.analysis-resume-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-border-subtle);
  font-size: var(--font-size-control);
}
.editorial-analysis > .technical-details {
  flex-shrink: 0;
  max-height: 35%;
  overflow: auto;
}
@media (max-width: 1050px) {
  .editorial-regions {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: auto minmax(0, 1fr);
    gap: 16px;
  }
}
</style>
