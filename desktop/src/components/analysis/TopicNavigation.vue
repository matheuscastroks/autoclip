<script setup lang="ts">
import type { AnalysisView } from '../../types';
import AppIcon from '../ui/AppIcon.vue';
defineProps<{
  topics: AnalysisView['topic_groups'];
  selectedTopicId: string;
  proposalCounts: Record<string, number>;
  discardedTopicIds: string[];
  total: number;
  busy: boolean;
}>();
defineEmits<{
  selectTopic: [id: string];
  discardTopic: [id: string];
  restoreTopic: [id: string];
}>();
</script>
<template>
  <nav class="topic-navigation" aria-label="Temas identificados">
    <label class="compact-topics"
      >Tema
      <select
        :value="selectedTopicId"
        @change="$emit('selectTopic', ($event.target as HTMLSelectElement).value)"
      >
        <option value="">Todos os temas ({{ total }})</option>
        <option v-for="group in topics" :key="group.id" :value="group.id">
          {{ group.label }} ({{ proposalCounts[group.id] || 0 }})
        </option>
      </select>
      <button
        v-if="selectedTopicId"
        type="button"
        :disabled="busy"
        :aria-label="
          discardedTopicIds.includes(selectedTopicId)
            ? 'Restaurar tema selecionado'
            : 'Descartar tema selecionado'
        "
        @click="
          discardedTopicIds.includes(selectedTopicId)
            ? $emit('restoreTopic', selectedTopicId)
            : $emit('discardTopic', selectedTopicId)
        "
      >
        <AppIcon
          :name="discardedTopicIds.includes(selectedTopicId) ? 'refresh' : 'trash'"
          size="sm"
        />
      </button>
    </label>
    <div class="topic-list">
      <h3>Temas</h3>
      <button
        type="button"
        :class="{ selected: !selectedTopicId }"
        :aria-pressed="!selectedTopicId"
        @click="$emit('selectTopic', '')"
      >
        Todos os temas <span>{{ total }}</span>
      </button>
      <div v-for="group in topics" :key="group.id" class="topic-row">
        <button
          type="button"
          :class="{ selected: selectedTopicId === group.id }"
          :aria-pressed="selectedTopicId === group.id"
          :title="group.label"
          @click="$emit('selectTopic', group.id)"
        >
          {{ group.label }} <span>{{ proposalCounts[group.id] || 0 }}</span>
        </button>
        <button
          type="button"
          :disabled="busy"
          :data-action="discardedTopicIds.includes(group.id) ? 'restore-topic' : 'discard-topic'"
          :aria-label="
            (discardedTopicIds.includes(group.id) ? 'Restaurar tema ' : 'Descartar tema ') +
            group.label
          "
          @click="
            discardedTopicIds.includes(group.id)
              ? $emit('restoreTopic', group.id)
              : $emit('discardTopic', group.id)
          "
        >
          <AppIcon :name="discardedTopicIds.includes(group.id) ? 'refresh' : 'trash'" size="sm" />
        </button>
      </div>
    </div>
    <div v-if="selectedTopicId" class="topic-summary">
      <p v-for="summary in topics.find(g => g.id === selectedTopicId)?.summaries" :key="summary">
        {{ summary }}
      </p>
    </div>
  </nav>
</template>
<style scoped>
.topic-navigation {
  min-width: 0;
  padding-right: 16px;
  border-right: 1px solid var(--color-border-subtle);
  overflow: auto;
}
.topic-list {
  background: transparent;
  border: 0;
  border-radius: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 0;
}
.topic-list h3 {
  font-size: var(--font-size-region);
  padding: 0 0 12px;
  text-transform: none;
  letter-spacing: normal;
  color: var(--color-text-primary);
}
.topic-list button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  min-width: 0;
  min-height: 36px;
  padding: 8px;
  border: 0;
  background: transparent;
  border-radius: 6px;
  text-align: left;
  color: var(--color-text-secondary);
  font-size: var(--font-size-control);
  overflow-wrap: anywhere;
}
.topic-list button:hover {
  background: var(--color-surface-hover);
}
.topic-list button.selected {
  background: var(--color-surface-selected);
  color: var(--color-text-primary);
}
.topic-row {
  display: flex;
  gap: 4px;
}
.topic-row > button:first-child {
  flex: 1;
}
.topic-summary {
  padding: 16px 0;
  font-size: var(--font-size-control);
}
.compact-topics {
  display: none;
}
@media (max-width: 1050px) {
  .topic-navigation {
    padding: 0;
    border: 0;
    overflow: visible;
  }
  .topic-list {
    display: none;
  }
  .compact-topics {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  select {
    flex: 1;
    min-width: 0;
    background: var(--color-surface-raised);
    border: 1px solid var(--color-border-subtle);
    border-radius: 6px;
    color: var(--color-text-primary);
    padding: 6px 8px;
  }
  .topic-summary {
    display: none;
  }
}
</style>
