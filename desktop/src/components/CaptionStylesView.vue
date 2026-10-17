<script setup lang="ts">
import { ref, computed, onUnmounted, watch } from 'vue';
import type { Config } from '../types';
import AppButton from './AppButton.vue';
import AppIcon from './ui/AppIcon.vue';

export type PresetKey = 'karaoke_yellow' | 'editorial_sober' | 'documentary' | 'impact';

interface PresetDefinition {
  id: PresetKey;
  label: string;
  badge: string;
  description: string;
  fontName: string;
  fontDisplay: string;
  mode: 'karaoke' | 'static' | 'lower_third' | 'kinetic_impact';
  modeLabel: string;
  uppercase: boolean;
  maxWords: number;
  fontColor: string;
  highlightColor: string;
  borderColor: string;
  borderWidth: number;
  bgColor?: string;
  bgOpacity?: number;
  accentPrefix?: string;
  marginV: number;
  // Hook banner specs
  hookTitle: string;
  hookBg: string;
  hookColor: string;
  hookBorder?: string;
  sampleWords: string[];
}

const props = defineProps<{
  config?: Config | null;
}>();

const emit = defineEmits<{
  savePreset: [presetId: PresetKey];
}>();

const presets: PresetDefinition[] = [
  {
    id: 'karaoke_yellow',
    label: 'Karaokê Amarelo',
    badge: 'Alta Retenção',
    description: 'Palavras ativas amarelas em tempo real sobre fundo escuro com borda espessa. Ideal para TikTok e Reels.',
    fontName: 'Montserrat ExtraBold',
    fontDisplay: "'Plus Jakarta Sans', Montserrat, sans-serif",
    mode: 'karaoke',
    modeLabel: 'Karaokê Dinâmico',
    uppercase: true,
    maxWords: 3,
    fontColor: '#FFFFFF',
    highlightColor: '#FFCC00',
    borderColor: '#000000',
    borderWidth: 3,
    marginV: 43,
    hookTitle: 'O SEGREDO DOS CORTES VIRAIS',
    hookBg: '#FFCC00',
    hookColor: '#000000',
    sampleWords: ['ROUBE', 'A', 'ATENÇÃO', 'EM', 'SEGUNDOS'],
  },
  {
    id: 'editorial_sober',
    label: 'Editorial Sóbrio',
    badge: 'Tech & Entrevistas',
    description: 'Legenda estática com tipografia clássica e contraste refinado. Perfeito para podcasts e negócios.',
    fontName: 'Montserrat ExtraBold',
    fontDisplay: "'Plus Jakarta Sans', Montserrat, sans-serif",
    mode: 'static',
    modeLabel: 'Bloco Contínuo',
    uppercase: false,
    maxWords: 5,
    fontColor: '#F5F3EE',
    highlightColor: '#F5F3EE',
    borderColor: '#18181B',
    borderWidth: 2,
    marginV: 38,
    hookTitle: 'Tecnologia & Visão de Futuro',
    hookBg: '#18201E',
    hookColor: '#F5F3EE',
    hookBorder: '1px solid rgba(245, 243, 238, 0.2)',
    sampleWords: ['Construindo', 'produtos', 'que', 'realmente', 'transformam'],
  },
  {
    id: 'documentary',
    label: 'Tarja Documental',
    badge: 'Jornalismo & Cinema',
    description: 'Faixa inferior translúcida com indicador lateral azul-aço e leitura pausada sem distrações.',
    fontName: 'Montserrat ExtraBold',
    fontDisplay: "'Plus Jakarta Sans', Montserrat, sans-serif",
    mode: 'lower_third',
    modeLabel: 'Tarja Inferior',
    uppercase: false,
    maxWords: 5,
    fontColor: '#F0F6FA',
    highlightColor: '#4A78A8',
    borderColor: '#141E28',
    borderWidth: 3,
    bgColor: 'rgba(20, 30, 40, 0.88)',
    accentPrefix: '▍ ',
    marginV: 26,
    hookTitle: '▍ INVESTIGAÇÃO EXCLUSIVA',
    hookBg: '#141E28',
    hookColor: '#F0F6FA',
    hookBorder: '1px solid #4A78A8',
    sampleWords: ['A história de como', 'tudo', 'começou.'],
  },
  {
    id: 'impact',
    label: 'Impacto Cinético',
    badge: 'News & Opinião',
    description: 'Palavra em coral elétrico com traço encorpado para afirmações provocativas e cortes jornalísticos.',
    fontName: 'Montserrat ExtraBold',
    fontDisplay: "'Plus Jakarta Sans', Montserrat, sans-serif",
    mode: 'kinetic_impact',
    modeLabel: 'Impacto Rápido',
    uppercase: true,
    maxWords: 3,
    fontColor: '#FFFFFF',
    highlightColor: '#FF5A36',
    borderColor: '#100E14',
    borderWidth: 4,
    marginV: 45,
    hookTitle: 'ALERTA DE CENÁRIO GLOBAL',
    hookBg: '#FF5A36',
    hookColor: '#FFFFFF',
    sampleWords: ['NOTÍCIAS', 'QUE', 'MUDAM', 'O', 'MUNDO'],
  },
];

const selectedPresetId = ref<PresetKey>(
  (props.config?.video_preset as PresetKey) || 'karaoke_yellow'
);

const currentPreset = computed(
  () => presets.find(p => p.id === selectedPresetId.value) || presets[0]
);

const isSavedDefault = computed(
  () => (props.config?.video_preset || 'karaoke_yellow') === selectedPresetId.value
);

// Preview monitor mode: 'captions' or 'hook'
const monitorView = ref<'captions' | 'hook'>('captions');

// Social media safe area overlay toggle
const showSafeAreas = ref(true);

// Test phrases
const testPhraseTemplates = [
  { label: 'Retenção Curta', text: 'O poder de reter a atenção nos primeiros segundos.' },
  { label: 'Entrevista', text: 'Não existe inovação real sem correr riscos calculados.' },
  { label: 'Provocação', text: 'Tudo o que você sabia sobre isso acabou de mudar.' },
];

const customText = ref('O poder de reter a atenção nos primeiros segundos.');

const activeWords = computed(() => {
  const t = customText.value.trim();
  if (!t) return ['Exemplo', 'de', 'legenda'];
  return t.split(/\s+/);
});

// Karaoke playback simulation
const currentWordIndex = ref(1);
const isPlaying = ref(false);
let playbackTimer: number | null = null;

function togglePlay() {
  if (isPlaying.value) {
    pausePlayback();
  } else {
    startPlayback();
  }
}

function startPlayback() {
  isPlaying.value = true;
  if (currentWordIndex.value >= activeWords.value.length - 1) {
    currentWordIndex.value = 0;
  }
  playbackTimer = window.setInterval(() => {
    if (currentWordIndex.value < activeWords.value.length - 1) {
      currentWordIndex.value++;
    } else {
      currentWordIndex.value = 0;
    }
  }, 480);
}

function pausePlayback() {
  isPlaying.value = false;
  if (playbackTimer !== null) {
    clearInterval(playbackTimer);
    playbackTimer = null;
  }
}

function selectWord(idx: number) {
  pausePlayback();
  currentWordIndex.value = idx;
}

function loadTemplate(text: string) {
  pausePlayback();
  customText.value = text;
  currentWordIndex.value = 0;
}

watch(selectedPresetId, () => {
  if (currentPreset.value.mode === 'static') {
    pausePlayback();
    currentWordIndex.value = -1;
  } else {
    currentWordIndex.value = Math.min(1, activeWords.value.length - 1);
  }
});

onUnmounted(() => {
  pausePlayback();
});
</script>

<template>
  <div class="caption-studio-view">
    <!-- Header Studio Bar -->
    <header class="studio-header">
      <div class="header-breadcrumb-titles">
        <div class="header-badge-tag">
          <AppIcon name="scissors" size="sm" />
          <span>MOTOR DE RENDERIZAÇÃO • IDENTIDADE VISUAL</span>
        </div>
        <h1 class="view-title">Estilos de Legenda & Ganchos</h1>
        <p class="view-subtitle">
          Configure a tipografia, animação de leitura e tarjas de abertura aplicadas pela engine ao renderizar os vídeos 9:16.
        </p>
      </div>

      <div class="header-action-zone">
        <AppButton
          class="button primary small save-preset-btn"
          :disabled="isSavedDefault"
          @click="$emit('savePreset', selectedPresetId)"
        >
          <AppIcon :name="isSavedDefault ? 'check-circle' : 'check'" size="sm" />
          <span>{{ isSavedDefault ? 'Estilo Padrão Ativo' : 'Definir como Padrão do Projeto' }}</span>
        </AppButton>
      </div>
    </header>

    <!-- Workspace Grid -->
    <div class="studio-workspace">
      <!-- Coluna da Esquerda: Catálogo de Presets do Motor -->
      <section class="presets-section" aria-label="Catálogo de estilos de vídeo">
        <div class="section-title-row">
          <div class="section-title-group">
            <span class="section-eyebrow">Estilos Calibrados</span>
            <span class="section-count">4 presets disponíveis</span>
          </div>
          <span class="engine-badge">ASS / FFmpeg Engine v1</span>
        </div>

        <div class="preset-deck" role="radiogroup" aria-label="Selecione um estilo de legenda">
          <article
            v-for="preset in presets"
            :key="preset.id"
            class="preset-deck-card"
            :class="{
              'is-selected': selectedPresetId === preset.id,
              'is-active-default': (config?.video_preset || 'karaoke_yellow') === preset.id,
            }"
            role="radio"
            :aria-checked="selectedPresetId === preset.id"
            tabindex="0"
            @click="selectedPresetId = preset.id"
            @keydown.enter="selectedPresetId = preset.id"
            @keydown.space.prevent="selectedPresetId = preset.id"
          >
            <!-- Card Header: Nome, Badge e Estado -->
            <div class="card-head">
              <div class="card-title-group">
                <span class="preset-title">{{ preset.label }}</span>
                <span class="preset-tag">{{ preset.badge }}</span>
              </div>

              <div class="card-indicators">
                <span
                  v-if="(config?.video_preset || 'karaoke_yellow') === preset.id"
                  class="current-default-pill"
                >
                  <AppIcon name="check" size="sm" />
                  Padrão do Projeto
                </span>
                <span class="selection-pill" :class="{ selected: selectedPresetId === preset.id }">
                  {{ selectedPresetId === preset.id ? 'Selecionado' : 'Selecionar' }}
                </span>
              </div>
            </div>

            <!-- Mini Specimen Visual Realista -->
            <div class="card-specimen-viewport">
              <!-- Hook Banner Mini Preview -->
              <div
                class="specimen-hook-banner"
                :style="{
                  backgroundColor: preset.hookBg,
                  color: preset.hookColor,
                  border: preset.hookBorder || 'none',
                }"
              >
                {{ preset.hookTitle }}
              </div>

              <!-- Subtitle Words Mini Preview -->
              <div
                class="specimen-subtitles"
                :style="{
                  backgroundColor: preset.bgColor || 'transparent',
                }"
              >
                <span v-if="preset.accentPrefix" class="specimen-accent">{{ preset.accentPrefix }}</span>
                <span
                  v-for="(word, wIdx) in preset.sampleWords"
                  :key="wIdx"
                  class="specimen-token"
                  :style="{
                    color:
                      preset.mode === 'static'
                        ? preset.fontColor
                        : wIdx === 2
                          ? preset.highlightColor
                          : preset.fontColor,
                    textTransform: preset.uppercase ? 'uppercase' : 'none',
                    textShadow: preset.borderWidth ? `0 0 2px ${preset.borderColor}` : 'none',
                  }"
                >
                  {{ word }}
                </span>
              </div>
            </div>

            <!-- Card Meta Specs -->
            <div class="card-specs-row">
              <span class="spec-chip">
                <AppIcon name="transcript" size="sm" />
                {{ preset.modeLabel }}
              </span>
              <span class="spec-chip">
                <AppIcon name="clock" size="sm" />
                Até {{ preset.maxWords }} palavras/tela
              </span>
              <span class="spec-chip font-spec">
                {{ preset.fontName }}
              </span>
            </div>

            <p class="card-description">{{ preset.description }}</p>
          </article>
        </div>
      </section>

      <!-- Coluna da Direita: Studio Monitor 9:16 & Inspector -->
      <section class="monitor-and-inspector" aria-label="Monitor de prévia e especificações">
        <!-- Monitor Program Toolbar -->
        <div class="monitor-card">
          <div class="monitor-topbar">
            <div class="monitor-info">
              <span class="monitor-dot" />
              <span class="monitor-heading">Monitor 9:16 (1080 × 1920)</span>
              <span class="monitor-preset-label">{{ currentPreset.label }}</span>
            </div>

            <div class="monitor-toolbar-actions">
              <!-- Toggle View Mode: Legenda vs Gancho -->
              <div class="view-mode-toggle" role="tablist">
                <button
                  type="button"
                  class="mode-btn"
                  :class="{ active: monitorView === 'captions' }"
                  role="tab"
                  :aria-selected="monitorView === 'captions'"
                  @click="monitorView = 'captions'"
                >
                  <AppIcon name="transcript" size="sm" />
                  Legenda
                </button>
                <button
                  type="button"
                  class="mode-btn"
                  :class="{ active: monitorView === 'hook' }"
                  role="tab"
                  :aria-selected="monitorView === 'hook'"
                  @click="monitorView = 'hook'"
                >
                  <AppIcon name="sparkle" size="sm" />
                  Gancho (0-7s)
                </button>
              </div>

              <!-- Safe Area Guide Toggle -->
              <button
                type="button"
                class="safe-area-toggle-btn"
                :class="{ active: showSafeAreas }"
                title="Mostrar guias de botões e áreas seguras do TikTok/Reels"
                @click="showSafeAreas = !showSafeAreas"
              >
                <AppIcon :name="showSafeAreas ? 'eye' : 'eye-off'" size="sm" />
                Safe Area
              </button>
            </div>
          </div>

          <!-- The Vertical 9:16 Canvas Stage -->
          <div class="canvas-stage-wrapper">
            <div class="canvas-aspect-box">
              <!-- Stage Backdrop (Dark Cinematic Studio Interview Lighting) -->
              <div class="stage-backdrop">
                <div class="backdrop-gradient" />
                <div class="backdrop-vignette" />
              </div>

              <!-- Safe Area Guides Overlay (Submagic / Opus Clip standard) -->
              <div v-if="showSafeAreas" class="safe-area-overlay">
                <!-- Top Header Platform Safe Boundary -->
                <div class="safe-top-zone">
                  <div class="safe-tag">Topo: Seguindo | Para Você (Evitar)</div>
                </div>

                <!-- Right Rail Platform Icons (Like, Comment, Save, Share) -->
                <div class="safe-right-rail" aria-hidden="true">
                  <div class="mock-platform-btn"><span class="mock-icon">♥</span></div>
                  <div class="mock-platform-btn"><span class="mock-icon">💬</span></div>
                  <div class="mock-platform-btn"><span class="mock-icon">🔖</span></div>
                  <div class="mock-platform-btn"><span class="mock-icon">↗</span></div>
                </div>

                <!-- Bottom Platform Safe Boundary (Sound track & Caption text) -->
                <div class="safe-bottom-zone">
                  <div class="safe-tag">Base: Legenda nativa & Áudio (Evitar)</div>
                </div>

                <!-- Center Safe Perimeter Guideline -->
                <div class="safe-box-boundary" />
              </div>

              <!-- Layer 1: Opening Hook Banner (Shown at top 24-26% margin) -->
              <div
                v-if="monitorView === 'hook'"
                class="hook-overlay-layer"
              >
                <div
                  class="hook-banner-container"
                  :style="{
                    backgroundColor: currentPreset.hookBg,
                    color: currentPreset.hookColor,
                    border: currentPreset.hookBorder || 'none',
                    fontFamily: currentPreset.fontDisplay,
                  }"
                >
                  <span class="hook-banner-text">{{ currentPreset.hookTitle }}</span>
                </div>
                <div class="hook-notice">Exibido nos primeiros 7 segundos do corte como âncora de retenção</div>
              </div>

              <!-- Layer 2: Synchronized Captions (Rendered at exact engine vertical margin) -->
              <div
                v-else
                class="captions-overlay-layer"
                :style="{
                  bottom: `${currentPreset.marginV * 1.5}px`,
                }"
              >
                <div
                  class="caption-render-box"
                  :class="{
                    'has-plate': !!currentPreset.bgColor,
                    'is-static': currentPreset.mode === 'static',
                  }"
                  :style="{
                    backgroundColor: currentPreset.bgColor || 'transparent',
                    fontFamily: currentPreset.fontDisplay,
                    textTransform: currentPreset.uppercase ? 'uppercase' : 'none',
                  }"
                >
                  <span v-if="currentPreset.accentPrefix" class="caption-prefix">
                    {{ currentPreset.accentPrefix }}
                  </span>

                  <span
                    v-for="(word, idx) in activeWords"
                    :key="idx"
                    class="caption-word-token"
                    :class="{
                      'is-active':
                        currentPreset.mode !== 'static' && idx === currentWordIndex,
                    }"
                    :style="{
                      color:
                        currentPreset.mode === 'static'
                          ? currentPreset.fontColor
                          : idx === currentWordIndex
                            ? currentPreset.highlightColor
                            : currentPreset.fontColor,
                      textShadow:
                        currentPreset.borderWidth > 0
                          ? `0 0 ${currentPreset.borderWidth}px ${currentPreset.borderColor}, -1px -1px 0 ${currentPreset.borderColor}, 1px -1px 0 ${currentPreset.borderColor}, -1px 1px 0 ${currentPreset.borderColor}, 1px 1px 0 ${currentPreset.borderColor}`
                          : 'none',
                    }"
                    @click="selectWord(idx)"
                  >
                    {{ word }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Playback Simulator Controls -->
          <div class="simulator-bar">
            <div class="simulator-actions">
              <button
                type="button"
                class="sim-play-btn"
                :title="isPlaying ? 'Pausar simulação' : 'Simular ritmo de fala (Karaokê)'"
                @click="togglePlay"
              >
                <AppIcon :name="isPlaying ? 'pause' : 'play'" size="sm" />
                <span>{{ isPlaying ? 'Pausar' : 'Simular Leitura' }}</span>
              </button>

              <span class="sim-speed-tag">Velocidade 1.0x</span>
            </div>

            <!-- Word Stepper Badges -->
            <div class="word-stepper-row" title="Clique em qualquer palavra para testar o destaque ativo">
              <span class="stepper-label">Passo:</span>
              <div class="stepper-tokens">
                <button
                  v-for="(w, idx) in activeWords"
                  :key="idx"
                  type="button"
                  class="step-token"
                  :class="{ active: idx === currentWordIndex }"
                  @click="selectWord(idx)"
                >
                  {{ w }}
                </button>
              </div>
            </div>
          </div>

          <!-- Test Phrase Selector & Input -->
          <div class="test-phrase-controls">
            <div class="phrase-header-row">
              <span class="control-label">Frase de teste para o monitor:</span>
              <div class="phrase-presets-list">
                <button
                  v-for="tpl in testPhraseTemplates"
                  :key="tpl.label"
                  type="button"
                  class="tpl-pill-btn"
                  @click="loadTemplate(tpl.text)"
                >
                  {{ tpl.label }}
                </button>
              </div>
            </div>

            <div class="input-field-wrap">
              <input
                id="caption-test-phrase-input"
                v-model="customText"
                type="text"
                maxlength="90"
                class="phrase-input"
                placeholder="Digite uma frase para testar a quebra..."
                @focus="pausePlayback"
              />
            </div>
          </div>
        </div>

        <!-- Technical Parameters Inspector Panel -->
        <div class="engine-inspector-panel">
          <div class="inspector-header">
            <span class="inspector-title">Parâmetros Injetados no Renderizador</span>
            <span class="inspector-preset-id">preset_id: {{ currentPreset.id }}</span>
          </div>

          <div class="parameters-grid">
            <div class="param-card">
              <span class="param-label">Tipografia</span>
              <span class="param-value font-highlight">{{ currentPreset.fontName }}</span>
              <span class="param-sub">Peso 900 • {{ currentPreset.uppercase ? 'Caixa Alta' : 'Caixa Natural' }}</span>
            </div>

            <div class="param-card">
              <span class="param-label">Cor Primária</span>
              <div class="color-swatch-row">
                <span class="swatch-chip" :style="{ backgroundColor: currentPreset.fontColor }" />
                <span class="param-value">{{ currentPreset.fontColor }}</span>
              </div>
              <span class="param-sub">Texto padrão</span>
            </div>

            <div class="param-card">
              <span class="param-label">Cor de Destaque</span>
              <div class="color-swatch-row">
                <span class="swatch-chip" :style="{ backgroundColor: currentPreset.highlightColor }" />
                <span class="param-value">{{ currentPreset.highlightColor }}</span>
              </div>
              <span class="param-sub">Palavra sincronizada</span>
            </div>

            <div class="param-card">
              <span class="param-label">Contorno / Tarja</span>
              <div class="color-swatch-row">
                <span class="swatch-chip" :style="{ backgroundColor: currentPreset.borderColor }" />
                <span class="param-value">{{ currentPreset.borderWidth }}px • {{ currentPreset.borderColor }}</span>
              </div>
              <span class="param-sub">{{ currentPreset.bgColor ? 'Com fundo translúcido' : 'Sem fundo' }}</span>
            </div>

            <div class="param-card">
              <span class="param-label">Margem Vertical</span>
              <span class="param-value">{{ currentPreset.marginV }}px</span>
              <span class="param-sub">Acima da safe area nativa</span>
            </div>

            <div class="param-card">
              <span class="param-label">Modo do Pipeline</span>
              <span class="param-value">{{ currentPreset.mode }}</span>
              <span class="param-sub">Geração de arquivo ASS</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.caption-studio-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
  max-width: 1240px;
  margin: 0 auto;
  width: 100%;
}

/* Studio Header */
.studio-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--color-border-subtle);
}

.header-breadcrumb-titles {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.header-badge-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--color-action-primary);
  text-transform: uppercase;
}

.view-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
}

.view-subtitle {
  font-size: 13.5px;
  color: var(--color-text-secondary);
  margin: 0;
  max-width: 660px;
  line-height: 1.45;
}

.header-action-zone {
  display: flex;
  align-items: center;
  flex: none;
}

.save-preset-btn {
  font-weight: 600;
  letter-spacing: 0.01em;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  height: 38px;
}

/* Studio Workspace Grid */
.studio-workspace {
  display: grid;
  grid-template-columns: 460px 1fr;
  gap: 28px;
  align-items: start;
}

@media (max-width: 1080px) {
  .studio-workspace {
    grid-template-columns: 1fr;
  }
}

/* Presets Column */
.presets-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title-group {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.section-eyebrow {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-secondary);
}

.section-count {
  font-size: 12px;
  color: var(--color-text-muted);
}

.engine-badge {
  font-size: 11px;
  font-family: monospace;
  color: var(--color-text-muted);
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  padding: 2px 8px;
  border-radius: 4px;
}

/* Preset Cards Deck */
.preset-deck {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preset-deck-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
  cursor: pointer;
  transition: all 0.15s ease-in-out;
  outline: none;
  position: relative;
}

.preset-deck-card:hover {
  border-color: var(--color-border-strong);
  background: var(--color-surface-hover);
}

.preset-deck-card.is-selected {
  border-color: var(--color-action-primary);
  background: var(--color-surface-raised);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
}

.preset-deck-card:focus-visible {
  box-shadow: 0 0 0 2px var(--color-action-primary);
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.card-title-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.preset-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.preset-tag {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 7px;
  background: rgba(175, 198, 213, 0.12);
  color: var(--color-action-primary);
  border-radius: 4px;
  letter-spacing: 0.02em;
}

.card-indicators {
  display: flex;
  align-items: center;
  gap: 6px;
}

.current-default-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(52, 211, 153, 0.15);
  color: var(--color-success);
  border: 1px solid rgba(52, 211, 153, 0.3);
}

.selection-pill {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--color-surface-raised);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border-subtle);
  transition: all 0.15s ease;
}

.selection-pill.selected {
  background: var(--color-action-primary);
  color: var(--color-action-primary-text);
  border-color: var(--color-action-primary);
}

/* Mini Specimen Box */
.card-specimen-viewport {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: #090c0f;
  border: 1px solid var(--color-border-subtle);
  border-radius: 6px;
  padding: 12px;
  min-height: 84px;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: hidden;
}

.specimen-hook-banner {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.05em;
  padding: 2px 8px;
  border-radius: 3px;
  text-align: center;
}

.specimen-subtitles {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 4px;
}

.specimen-accent {
  color: #4a78a8;
  font-weight: 900;
}

.specimen-token {
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.02em;
}

/* Specs Row */
.card-specs-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.spec-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--color-text-secondary);
  background: var(--color-surface-raised);
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid var(--color-border-subtle);
}

.spec-chip.font-spec {
  font-weight: 600;
  color: var(--color-text-primary);
}

.card-description {
  font-size: 12px;
  color: var(--color-text-muted);
  line-height: 1.4;
  margin: 0;
}

/* Monitor & Inspector Column */
.monitor-and-inspector {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.monitor-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Topbar */
.monitor-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: var(--color-surface-raised);
  border-bottom: 1px solid var(--color-border-subtle);
  flex-wrap: wrap;
  gap: 10px;
}

.monitor-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.monitor-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-success);
}

.monitor-heading {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.monitor-preset-label {
  font-size: 12px;
  color: var(--color-action-primary);
  font-weight: 700;
}

.monitor-toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.view-mode-toggle {
  display: inline-flex;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: 4px;
  padding: 2px;
}

.mode-btn {
  background: transparent;
  border: none;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  padding: 3px 8px;
  border-radius: 3px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.12s ease;
}

.mode-btn.active {
  background: var(--color-surface-selected);
  color: var(--color-text-primary);
}

.safe-area-toggle-btn {
  background: transparent;
  border: 1px solid var(--color-border-subtle);
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  padding: 4px 8px;
  border-radius: 4px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  transition: all 0.12s ease;
}

.safe-area-toggle-btn.active {
  background: rgba(175, 198, 213, 0.15);
  color: var(--color-action-primary);
  border-color: var(--color-action-primary);
}

/* 9:16 Canvas Stage */
.canvas-stage-wrapper {
  background: #080a0c;
  padding: 24px 16px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.canvas-aspect-box {
  width: 280px;
  height: 497px; /* Exact 9:16 aspect ratio: 280 * 16 / 9 = 497.7px */
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.08);
}

.stage-backdrop {
  position: absolute;
  inset: 0;
  background-color: #12161b;
  z-index: 1;
}

.backdrop-gradient {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 50% 35%, rgba(45, 60, 75, 0.45) 0%, rgba(12, 16, 20, 0.95) 75%);
}

.backdrop-vignette {
  position: absolute;
  inset: 0;
  box-shadow: inset 0 0 60px rgba(0, 0, 0, 0.8);
}

/* Safe Area Overlay */
.safe-area-overlay {
  position: absolute;
  inset: 0;
  z-index: 5;
  pointer-events: none;
}

.safe-top-zone {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 64px;
  background: rgba(239, 68, 68, 0.05);
  border-bottom: 1px dashed rgba(239, 68, 68, 0.25);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 6px;
}

.safe-bottom-zone {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 80px;
  background: rgba(239, 68, 68, 0.05);
  border-top: 1px dashed rgba(239, 68, 68, 0.25);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding-bottom: 6px;
}

.safe-right-rail {
  position: absolute;
  right: 8px;
  bottom: 96px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
}

.mock-platform-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.mock-icon {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);
}

.safe-tag {
  font-size: 9px;
  font-weight: 600;
  color: rgba(248, 113, 113, 0.8);
  letter-spacing: 0.02em;
}

.safe-box-boundary {
  position: absolute;
  top: 64px;
  bottom: 80px;
  left: 12px;
  right: 48px;
  border: 1px dashed rgba(52, 211, 153, 0.35);
  border-radius: 4px;
}

/* Hook Overlay Layer */
.hook-overlay-layer {
  position: absolute;
  top: 76px;
  left: 16px;
  right: 16px;
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
}

.hook-banner-container {
  padding: 6px 14px;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.hook-banner-text {
  font-size: 13px;
  font-weight: 900;
  letter-spacing: 0.04em;
  display: block;
}

.hook-notice {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.65);
  background: rgba(0, 0, 0, 0.5);
  padding: 2px 8px;
  border-radius: 4px;
}

/* Captions Overlay Layer */
.captions-overlay-layer {
  position: absolute;
  left: 16px;
  right: 48px; /* Offset to clear right rail */
  z-index: 10;
  display: flex;
  justify-content: center;
  text-align: center;
}

.caption-render-box {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 4px;
  line-height: 1.25;
}

.caption-render-box.has-plate {
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.5);
}

.caption-prefix {
  font-weight: 900;
  color: #4a78a8;
  font-size: 16px;
}

.caption-word-token {
  font-size: 16px;
  font-weight: 800;
  cursor: pointer;
  transition: transform 0.12s ease, color 0.12s ease;
  user-select: none;
  display: inline-block;
}

.caption-word-token:hover {
  transform: scale(1.08);
}

.caption-word-token.is-active {
  transform: scale(1.12);
}

/* Simulator Bar */
.simulator-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--color-surface-raised);
  border-top: 1px solid var(--color-border-subtle);
  border-bottom: 1px solid var(--color-border-subtle);
  flex-wrap: wrap;
  gap: 12px;
}

.simulator-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sim-play-btn {
  background: var(--color-action-primary);
  color: var(--color-action-primary-text);
  border: none;
  font-size: 12px;
  font-weight: 700;
  padding: 6px 14px;
  border-radius: 4px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: background 0.12s ease;
}

.sim-play-btn:hover {
  background: var(--color-action-primary-hover);
}

.sim-speed-tag {
  font-size: 11px;
  color: var(--color-text-muted);
  font-weight: 600;
}

.word-stepper-row {
  display: flex;
  align-items: center;
  gap: 6px;
  overflow-x: auto;
  max-width: 100%;
}

.stepper-label {
  font-size: 11px;
  color: var(--color-text-muted);
  font-weight: 600;
}

.stepper-tokens {
  display: flex;
  gap: 4px;
}

.step-token {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  color: var(--color-text-secondary);
  font-size: 10.5px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.12s ease;
}

.step-token:hover {
  border-color: var(--color-border-strong);
  color: var(--color-text-primary);
}

.step-token.active {
  background: var(--color-action-primary);
  color: var(--color-action-primary-text);
  border-color: var(--color-action-primary);
}

/* Test Phrase Controls */
.test-phrase-controls {
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.phrase-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}

.control-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.phrase-presets-list {
  display: flex;
  gap: 6px;
}

.tpl-pill-btn {
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
  color: var(--color-text-secondary);
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.12s ease;
}

.tpl-pill-btn:hover {
  border-color: var(--color-border-strong);
  color: var(--color-text-primary);
}

.phrase-input {
  width: 100%;
  background: var(--color-canvas);
  border: 1px solid var(--color-border-subtle);
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--color-text-primary);
  outline: none;
  box-sizing: border-box;
  transition: border-color 0.15s ease;
}

.phrase-input:focus {
  border-color: var(--color-action-primary);
  box-shadow: 0 0 0 1px var(--color-action-primary);
}

/* Engine Inspector Panel */
.engine-inspector-panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.inspector-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border-subtle);
}

.inspector-title {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-secondary);
}

.inspector-preset-id {
  font-size: 11px;
  font-family: monospace;
  color: var(--color-action-primary);
}

.parameters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px;
}

.param-card {
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
  border-radius: 6px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.param-label {
  font-size: 10.5px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.param-value {
  font-size: 13px;
  font-weight: 700;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.param-value.font-highlight {
  color: var(--color-action-primary);
}

.param-sub {
  font-size: 10.5px;
  color: var(--color-text-muted);
}

.color-swatch-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.swatch-chip {
  width: 14px;
  height: 14px;
  border-radius: 3px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  flex: none;
}
</style>
