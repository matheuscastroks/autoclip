<script setup lang="ts">
import { ref, computed } from 'vue';
import type { Config } from '../types';
import AppButton from './AppButton.vue';
import AppIcon from './ui/AppIcon.vue';

export type PresetKey = 'karaoke_yellow' | 'editorial_sober' | 'documentary' | 'impact';

interface PresetOption {
  id: PresetKey;
  name: string;
  badge: string;
  description: string;
  specimenWords: { text: string; highlight?: boolean }[];
  accentPrefix?: string;
  uppercase: boolean;
  textColor: string;
  highlightColor?: string;
  bgColor?: string;
  borderColor?: string;
  borderWidth?: number;
}

const props = defineProps<{
  config?: Config | null;
}>();

const emit = defineEmits<{
  savePreset: [presetId: PresetKey];
}>();

const presets: PresetOption[] = [
  {
    id: 'karaoke_yellow',
    name: 'Karaokê Amarelo',
    badge: 'Alta retenção',
    description: 'Palavra ativa iluminada em amarelo de alto contraste. Ideal para redes como TikTok, Reels e Shorts.',
    specimenWords: [
      { text: 'ROUBE' },
      { text: 'A' },
      { text: 'ATENÇÃO', highlight: true },
      { text: 'EM' },
      { text: 'SEGUNDOS' },
    ],
    uppercase: true,
    textColor: '#FFFFFF',
    highlightColor: '#FFCC00',
    borderColor: '#000000',
    borderWidth: 2,
  },
  {
    id: 'editorial_sober',
    name: 'Editorial Sóbrio',
    badge: 'Negócios & Entrevistas',
    description: 'Tipografia minimalista em caixa natural, com leitura suave e sem distrações visuais.',
    specimenWords: [
      { text: 'Construindo' },
      { text: 'produtos' },
      { text: 'que' },
      { text: 'realmente' },
      { text: 'transformam' },
    ],
    uppercase: false,
    textColor: '#F5F3EE',
  },
  {
    id: 'documentary',
    name: 'Tarja Documental',
    badge: 'Storytelling & Cinema',
    description: 'Faixa inferior translúcida com indicador lateral azul-aço e ritmo pausado.',
    accentPrefix: '▍ ',
    specimenWords: [
      { text: 'A' },
      { text: 'história' },
      { text: 'de' },
      { text: 'como' },
      { text: 'tudo' },
      { text: 'começou.' },
    ],
    uppercase: false,
    textColor: '#F0F6FA',
    bgColor: 'rgba(20, 30, 40, 0.85)',
  },
  {
    id: 'impact',
    name: 'Impacto Cinético',
    badge: 'News & Opinião',
    description: 'Palavras curtas em coral elétrico com traço encorpado para declarações fortes.',
    specimenWords: [
      { text: 'NOTÍCIAS' },
      { text: 'QUE' },
      { text: 'MUDAM', highlight: true },
      { text: 'O' },
      { text: 'CENÁRIO' },
    ],
    uppercase: true,
    textColor: '#FFFFFF',
    highlightColor: '#FF5A36',
    borderColor: '#100E14',
    borderWidth: 2,
  },
];

const selectedPresetId = ref<PresetKey>(
  (props.config?.video_preset as PresetKey) || 'karaoke_yellow'
);

const isSavedDefault = computed(
  () => (props.config?.video_preset || 'karaoke_yellow') === selectedPresetId.value
);
</script>

<template>
  <div class="caption-presets-view">
    <!-- Header Minimalista -->
    <header class="presets-header">
      <div class="header-titles">
        <h1 class="page-title">Estilos de Legenda</h1>
        <p class="page-subtitle">
          Escolha o modelo visual que será aplicado automaticamente aos vídeos gerados pelo motor.
        </p>
      </div>

      <AppButton
        class="button primary small save-btn"
        :disabled="isSavedDefault"
        @click="$emit('savePreset', selectedPresetId)"
      >
        <AppIcon :name="isSavedDefault ? 'check-circle' : 'check'" size="sm" />
        {{ isSavedDefault ? 'Estilo padrão ativo' : 'Salvar como padrão' }}
      </AppButton>
    </header>

    <!-- Grid Limpo de Presets -->
    <div class="presets-grid" role="radiogroup" aria-label="Selecione um estilo de legenda">
      <article
        v-for="preset in presets"
        :key="preset.id"
        class="preset-card"
        :class="{
          'is-selected': selectedPresetId === preset.id,
          'is-default': (config?.video_preset || 'karaoke_yellow') === preset.id,
        }"
        role="radio"
        :aria-checked="selectedPresetId === preset.id"
        tabindex="0"
        @click="selectedPresetId = preset.id"
        @keydown.enter="selectedPresetId = preset.id"
        @keydown.space.prevent="selectedPresetId = preset.id"
      >
        <!-- Topo do Card -->
        <div class="card-header">
          <div class="card-titles">
            <span class="preset-name">{{ preset.name }}</span>
            <span class="preset-badge">{{ preset.badge }}</span>
          </div>

          <div class="selection-indicator">
            <span
              v-if="(config?.video_preset || 'karaoke_yellow') === preset.id"
              class="active-tag"
            >
              Padrão atual
            </span>
            <div class="radio-circle" :class="{ checked: selectedPresetId === preset.id }">
              <span v-if="selectedPresetId === preset.id" class="radio-check" />
            </div>
          </div>
        </div>

        <!-- Amostra Tipográfica Direta e Limpa -->
        <div class="specimen-area">
          <div
            class="specimen-text"
            :style="{
              textTransform: preset.uppercase ? 'uppercase' : 'none',
              backgroundColor: preset.bgColor || 'transparent',
              padding: preset.bgColor ? '6px 12px' : '0',
              borderRadius: preset.bgColor ? '4px' : '0',
            }"
          >
            <span v-if="preset.accentPrefix" class="accent-prefix">{{ preset.accentPrefix }}</span>
            <span
              v-for="(word, i) in preset.specimenWords"
              :key="i"
              class="word"
              :style="{
                color: word.highlight ? preset.highlightColor : preset.textColor,
                textShadow: preset.borderWidth
                  ? `0 0 ${preset.borderWidth}px ${preset.borderColor}`
                  : 'none',
              }"
            >
              {{ word.text }}
            </span>
          </div>
        </div>

        <!-- Descrição Simples -->
        <p class="preset-description">{{ preset.description }}</p>
      </article>
    </div>
  </div>
</template>

<style scoped>
.caption-presets-view {
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Header */
.presets-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--color-border-subtle);
}

.header-titles {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
  letter-spacing: -0.01em;
}

.page-subtitle {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.4;
}

.save-btn {
  font-weight: 600;
  flex-shrink: 0;
}

/* Grid de Presets */
.presets-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

@media (max-width: 720px) {
  .presets-grid {
    grid-template-columns: 1fr;
  }
}

/* Cards Minimalistas */
.preset-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 18px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
  cursor: pointer;
  outline: none;
  transition: border-color 0.15s ease, background-color 0.15s ease;
}

.preset-card:hover {
  border-color: var(--color-border-strong);
  background: var(--color-surface-hover);
}

.preset-card.is-selected {
  border-color: var(--color-action-primary);
  background: var(--color-surface-raised);
}

.preset-card:focus-visible {
  box-shadow: 0 0 0 2px var(--color-action-primary);
}

/* Topo do Card */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.card-titles {
  display: flex;
  align-items: center;
  gap: 8px;
}

.preset-name {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.preset-badge {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  background: var(--color-canvas);
  padding: 2px 7px;
  border-radius: 4px;
  border: 1px solid var(--color-border-subtle);
}

.selection-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.active-tag {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-success);
  background: rgba(52, 211, 153, 0.12);
  border: 1px solid rgba(52, 211, 153, 0.25);
  padding: 1px 7px;
  border-radius: 4px;
}

.radio-circle {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 1px solid var(--color-border-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.12s ease;
}

.radio-circle.checked {
  border-color: var(--color-action-primary);
}

.radio-check {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-action-primary);
}

/* Amostra Tipográfica */
.specimen-area {
  background: #090c0f;
  border: 1px solid var(--color-border-subtle);
  border-radius: 6px;
  padding: 20px 16px;
  min-height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.specimen-text {
  font-family: 'Plus Jakarta Sans', Montserrat, sans-serif;
  font-size: 15px;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 5px;
  line-height: 1.3;
}

.accent-prefix {
  color: #4a78a8;
  font-weight: 900;
}

.word {
  display: inline-block;
}

/* Descrição */
.preset-description {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.45;
  margin: 0;
}
</style>
