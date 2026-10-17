<script setup lang="ts">
import AppIcon from '../ui/AppIcon.vue';

withDefaults(
  defineProps<{
    selectedPreset?: string;
    selectedSpeed?: string;
  }>(),
  {
    selectedPreset: 'karaoke-yellow-v1',
    selectedSpeed: '1.0x',
  }
);

const emit = defineEmits<{
  'update:preset': [preset: string];
  'update:speed': [speed: string];
}>();

interface PresetOption {
  id: string;
  title: string;
  description: string;
  sampleColor: string;
}

const presets: PresetOption[] = [
  {
    id: 'karaoke-yellow-v1',
    title: 'Karaoke Amarelo',
    description: 'Destaque viral palavra por palavra',
    sampleColor: '#ffd700',
  },
  {
    id: 'clean-white-v1',
    title: 'Minimalista Branco',
    description: 'Estilo sóbrio e editorial',
    sampleColor: '#ffffff',
  },
  {
    id: 'boxed-contrast-v1',
    title: 'Alto Contraste',
    description: 'Tarja preta para máxima legibilidade',
    sampleColor: '#4682b4',
  },
  {
    id: 'neon-cyan-v1',
    title: 'Neon Ciano',
    description: 'Estilo gamer e dinâmico',
    sampleColor: '#00f0ff',
  },
];

const speeds = ['1.0x', '1.1x', '1.15x'];
</script>

<template>
  <section class="dashboard-card output-guidelines-card" aria-labelledby="output-guidelines-heading">
    <header class="card-header">
      <div class="card-header-left">
        <AppIcon name="sparkle" size="sm" class="card-icon" />
        <h3 id="output-guidelines-heading" class="card-title">Diretrizes de Saída dos Shorts</h3>
      </div>
      <span class="preset-format-tag">9:16 Vertical</span>
    </header>

    <div class="card-body output-guidelines-body">
      <!-- Seção 1: Preset de Legendas -->
      <div class="guideline-group">
        <div class="group-header">
          <label class="group-label">Estilo Padrão de Legenda</label>
          <span class="group-hint">Aplicado na renderização final</span>
        </div>

        <div class="presets-mini-grid" role="radiogroup" aria-label="Estilo de Legenda">
          <button
            v-for="p in presets"
            :key="p.id"
            type="button"
            role="radio"
            :aria-checked="selectedPreset === p.id"
            class="preset-mini-card"
            :class="{ 'is-selected': selectedPreset === p.id }"
            :data-preset="p.id"
            @click="emit('update:preset', p.id)"
          >
            <div class="preset-card-top">
              <span class="preset-color-dot" :style="{ backgroundColor: p.sampleColor }" />
              <strong class="preset-name">{{ p.title }}</strong>
            </div>
            <span class="preset-desc">{{ p.description }}</span>
          </button>
        </div>
      </div>

      <!-- Seção 2: Ritmo de Fala & Velocidade -->
      <div class="guideline-group">
        <div class="group-header">
          <label class="group-label">Ritmo & Velocidade</label>
          <span class="group-hint">Aceleração com pitch de áudio preservado</span>
        </div>

        <div class="speed-selector-pills" role="radiogroup" aria-label="Velocidade dos cortes">
          <button
            v-for="s in speeds"
            :key="s"
            type="button"
            role="radio"
            :aria-checked="selectedSpeed === s"
            class="speed-pill-btn"
            :class="{ 'is-active': selectedSpeed === s }"
            :data-speed="s"
            @click="emit('update:speed', s)"
          >
            {{ s }}
            <span class="speed-tag-subtle">{{ s === '1.0x' ? 'Normal' : s === '1.1x' ? 'Dinâmico' : 'Rápido' }}</span>
          </button>
        </div>
      </div>

      <!-- Seção 3: Enquadramento & Resolução -->
      <div class="framing-notice-box">
        <div class="framing-icon">
          <AppIcon name="video" size="md" />
        </div>
        <div class="framing-copy">
          <strong>1080×1920 (9:16) · Auto-Framing Ativo</strong>
          <p>Rastreamento facial inteligente centralizado para formato TikTok, Reels e Shorts.</p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.output-guidelines-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: border-color 0.2s ease;
}

.output-guidelines-card:hover {
  border-color: var(--color-border-strong);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border-subtle);
  background: var(--color-surface-raised);
}

.card-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

.preset-format-tag {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-action-primary);
  background: rgba(175, 198, 213, 0.12);
  padding: 2px 8px;
  border-radius: var(--radius-control);
}

.output-guidelines-body {
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.guideline-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.group-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}

.group-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-primary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.group-hint {
  font-size: 11px;
  color: var(--color-text-muted);
}

.presets-mini-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.preset-mini-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  background: var(--color-canvas);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-control);
  cursor: pointer;
  text-align: left;
  transition: all 0.15s ease;
  outline: none;
}

.preset-mini-card:hover {
  border-color: var(--color-border-strong);
  background: var(--color-surface-raised);
}

.preset-mini-card.is-selected {
  border-color: var(--color-action-primary);
  background: rgba(175, 198, 213, 0.08);
  box-shadow: 0 0 0 1px var(--color-action-primary);
}

.preset-card-top {
  display: flex;
  align-items: center;
  gap: 6px;
}

.preset-color-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.preset-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.preset-desc {
  font-size: 11px;
  color: var(--color-text-secondary);
  line-height: 1.3;
}

.speed-selector-pills {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.speed-pill-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 8px 12px;
  background: var(--color-canvas);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-control);
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
  outline: none;
}

.speed-pill-btn:hover {
  border-color: var(--color-border-strong);
  color: var(--color-text-primary);
}

.speed-pill-btn.is-active {
  background: var(--color-action-primary);
  border-color: var(--color-action-primary);
  color: var(--color-action-primary-text, #ffffff);
}

.speed-tag-subtle {
  font-size: 10px;
  font-weight: 500;
  opacity: 0.85;
}

.framing-notice-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-control);
}

.framing-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: rgba(175, 198, 213, 0.15);
  color: var(--color-action-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.framing-copy {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.framing-copy strong {
  font-size: 12px;
  color: var(--color-text-primary);
}

.framing-copy p {
  margin: 0;
  font-size: 11px;
  color: var(--color-text-secondary);
  line-height: 1.3;
}

@media (max-width: 600px) {
  .presets-mini-grid {
    grid-template-columns: 1fr;
  }
}
</style>
