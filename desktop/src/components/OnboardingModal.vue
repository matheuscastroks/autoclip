<script setup lang="ts">
import AppIcon from './ui/AppIcon.vue';
import ProcessProgress from './ui/ProcessProgress.vue';
import { ref, computed, onUnmounted, watch } from 'vue';
import { ElSteps, ElStep, ElTag, ElAlert } from 'element-plus';
import type { HardwareProfile, ProvisionStatus } from '../types';
import { api } from '../api';
import { usePolling } from '../composables/usePolling';
import { useModalFocus } from '../composables/useModalFocus';
const modalRoot = ref<HTMLElement>();
useModalFocus(modalRoot);

const props = defineProps<{
  profile: HardwareProfile | null;
  toolsMissing: boolean;
  asrMissing: boolean;
  geminiKeyConfigured?: boolean;
  openrouterKeyConfigured?: boolean;
  saveKey?: (key: string) => Promise<unknown>;
  saveOpenRouterKey?: (key: string) => Promise<unknown>;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'configured'): void;
}>();

const step = ref<'diagnosis' | 'downloading' | 'apikey'>('diagnosis');
const stepIndex = computed(() => {
  if (step.value === 'diagnosis') return 0;
  if (step.value === 'downloading') return 1;
  return 2;
});
const selectedTier = ref<number>(props.profile?.recommended_tier || 2);
const modelChosen = ref(false);
watch(
  () => props.profile?.recommended_tier,
  tier => {
    if (tier && !modelChosen.value && step.value === 'diagnosis') selectedTier.value = tier;
  }
);
function chooseModel(tier: number) {
  modelChosen.value = true;
  selectedTier.value = tier;
}
const installFfmpeg = ref<boolean>(props.toolsMissing);
const busy = ref<boolean>(false);
const error = ref<string | null>(null);

const apiKeyProvider = ref<'gemini' | 'openrouter'>('gemini');
const apiKeyInput = ref<string>('');
const keySaved = ref<boolean>(false);
watch(apiKeyInput, value => {
  if (value) keySaved.value = false;
});
watch(apiKeyProvider, () => {
  apiKeyInput.value = '';
  keySaved.value = false;
  error.value = null;
});

const tiers = [
  {
    tier: 1,
    id: 'Systran/faster-whisper-base',
    title: 'Tier 1 (Leve)',
    desc: 'Whisper Base · ~140 MB · Baixo consumo de RAM e CPU',
    speed: 'Menor consumo',
  },
  {
    tier: 2,
    id: 'Systran/faster-whisper-small',
    title: 'Tier 2 (Equilibrado)',
    desc: 'Whisper Small · ~460 MB · Modelo intermediário para uso geral',
    speed: 'Padrão',
  },
  {
    tier: 3,
    id: 'Systran/faster-whisper-large-v3-turbo',
    title: 'Tier 3 (Alta Performance)',
    desc: 'Whisper Large v3 Turbo · ~800 MB · Modelo de maior porte; requer mais memória',
    speed: 'Maior capacidade',
  },
];

const selectedModelId = computed(() => {
  const t = tiers.find(item => item.tier === selectedTier.value);
  return t ? t.id : 'Systran/faster-whisper-small';
});

const provisionStatus = ref<ProvisionStatus>({
  status: 'idle',
  stage: 'idle',
  item: '',
  downloaded_bytes: 0,
  total_bytes: 0,
  speed_bps: 0,
  percent: null,
  error: null,
});

const { start: startPolling, stop: stopPolling } = usePolling(pollStatus, {
  intervalMs: 800,
  immediate: false,
});

async function pollStatus() {
  try {
    const st = await api.provisionStatus();
    provisionStatus.value = st;
    if (st.status === 'ready') {
      stopPolling();
      step.value = 'apikey';
      emit('configured');
    } else if (st.status === 'failed' || st.status === 'cancelled') {
      stopPolling();
      error.value = st.error || 'A instalação foi interrompida.';
    }
  } catch (e) {
    // keep polling
  }
}

async function startProvision() {
  busy.value = true;
  error.value = null;
  step.value = 'downloading';
  try {
    provisionStatus.value = await api.provision({
      model_id: selectedModelId.value,
      install_ffmpeg: installFfmpeg.value,
    });
    startPolling();
  } catch (e) {
    error.value = (e as Error).message;
    step.value = 'diagnosis';
  } finally {
    busy.value = false;
  }
}

async function cancelProvision() {
  try {
    await api.cancelProvision();
    stopPolling();
    step.value = 'diagnosis';
  } catch (e) {
    error.value = (e as Error).message;
  }
}

async function handleSaveKey() {
  if (busy.value || !apiKeyInput.value.trim()) return;
  busy.value = true;
  error.value = null;
  keySaved.value = false;
  try {
    const save = apiKeyProvider.value === 'gemini' ? props.saveKey : props.saveOpenRouterKey;
    if (!save) throw new Error('Salvamento indisponível. Abra Configurações para salvar a chave.');
    await save(apiKeyInput.value.trim());
    keySaved.value = true;
    apiKeyInput.value = '';
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    busy.value = false;
  }
}

function finish() {
  emit('close');
}

onUnmounted(() => {
  stopPolling();
});
</script>

<template>
  <div
    class="onboarding-overlay"
    role="dialog"
    aria-modal="true"
    aria-labelledby="onboarding-title"
  >
    <div ref="modalRoot" class="onboarding-container" tabindex="-1">
      <header class="onboarding-header">
        <div class="header-badge">
          <AppIcon name="sparkle" size="md" />
          <span>Configuração local</span>
        </div>
        <h2 id="onboarding-title">Preparar o AutoClip</h2>
        <p class="header-subtitle">
          Transcrição e renderização são locais. A análise editorial utiliza o provedor de IA
          configurado e envia somente texto. Instale os recursos necessários para começar.
        </p>
        <button
          v-if="step !== 'downloading'"
          type="button"
          class="button small secondary"
          data-action="defer-setup"
          :disabled="busy"
          @click="emit('close')"
        >
          Configurar depois e consultar projetos
        </button>
      </header>

      <div class="steps-wrapper" style="margin-bottom: 24px; padding: 0 16px">
        <el-steps :active="stepIndex" finish-status="success" align-center>
          <el-step title="Diagnóstico" description="Hardware e Modelo" />
          <el-step title="Instalação" description="Baixar recursos" />
          <el-step title="Curadoria IA" description="Chave de API" />
        </el-steps>
      </div>

      <!-- Step 1: Diagnosis & Model Selection -->
      <section v-if="step === 'diagnosis'" class="onboarding-step">
        <div v-if="profile" class="hardware-diagnosis-card">
          <div class="diagnosis-header">
            <AppIcon name="cpu" size="md" />
            <strong>Diagnóstico de Hardware</strong>
          </div>
          <div class="diagnosis-grid">
            <div class="diag-item">
              <span class="diag-label">Processador (CPU)</span>
              <span class="diag-val"
                >{{ profile.cpu_physical_cores }} núcleos físicos ({{
                  profile.cpu_logical_cores
                }}
                threads)</span
              >
            </div>
            <div class="diag-item">
              <span class="diag-label">Memória RAM</span>
              <span class="diag-val"
                >{{ profile.ram_total_gb }} GB ({{ profile.ram_available_gb }} GB livres)</span
              >
            </div>
            <div class="diag-item">
              <span class="diag-label">Aceleração Gráfica (GPU)</span>
              <span class="diag-val">{{
                profile.gpu_name
                  ? profile.gpu_name + ' (' + profile.vram_gb + ' GB VRAM)'
                  : profile.has_cuda
                    ? 'GPU NVIDIA CUDA detectada'
                    : 'Modo CPU otimizado'
              }}</span>
            </div>
          </div>
        </div>

        <div class="tiers-selection-section">
          <div class="section-heading">
            <strong>Escolha o modelo de transcrição Whisper:</strong>
            <span class="hint"
              >O tier recomendado foi pré-selecionado de acordo com seu hardware.</span
            >
          </div>

          <div class="tiers-grid">
            <button
              v-for="item in tiers"
              :key="item.tier"
              type="button"
              class="tier-card"
              :data-tier="item.tier"
              :aria-pressed="selectedTier === item.tier"
              :class="{
                selected: selectedTier === item.tier,
                recommended: profile && profile.recommended_tier === item.tier,
              }"
              @click="chooseModel(item.tier)"
            >
              <div class="tier-top">
                <span class="tier-title">{{ item.title }}</span>
                <span v-if="profile && profile.recommended_tier === item.tier" class="rec-pill">
                  Recomendado
                </span>
              </div>
              <p class="tier-desc">{{ item.desc }}</p>
              <div class="tier-footer">
                <span class="speed-tag">{{ item.speed }}</span>
              </div>
            </button>
          </div>
        </div>

        <div class="ffmpeg-option-card">
          <label class="checkbox-label">
            <input v-model="installFfmpeg" type="checkbox" data-action="toggle-ffmpeg" />
            <div class="checkbox-info">
              <strong>Instalar ferramentas multimídia FFmpeg & ffprobe</strong>
              <span
                >Baixa automaticamente a distribuição oficial Gyan FFmpeg para processar vídeos e
                extrair áudio com alta fidelidade.</span
              >
            </div>
          </label>
        </div>

        <div v-if="error" class="onboarding-error-banner">
          <AppIcon name="warning" size="sm" />
          <span>{{ error }}</span>
        </div>

        <div class="onboarding-actions">
          <button
            type="button"
            class="button primary large full-width"
            data-action="start-provision"
            :disabled="busy"
            @click="startProvision"
          >
            <AppIcon name="download" size="md" />
            <span>Instalar Dependências Automaticamente</span>
          </button>
        </div>
      </section>

      <!-- Step 2: Live Download Progress -->
      <section v-else-if="step === 'downloading'" class="onboarding-step">
        <div class="download-progress-card">
          <div class="progress-header">
            <div class="spinner-item">
              <AppIcon name="spinner" size="md" class="animate-spin" />
              <strong>Baixando e configurando dependências...</strong>
            </div>
            <span class="percent-badge">{{
              provisionStatus.percent === null
                ? 'Calculando tamanho'
                : `${provisionStatus.percent}% do arquivo`
            }}</span>
          </div>

          <div class="progress-bar-wrap" style="margin: 12px 0">
            <ProcessProgress
              :progress="{
                stage: provisionStatus.stage,
                steps: {},
                stage_percent: provisionStatus.percent,
                completed_units:
                  provisionStatus.completed_units ?? provisionStatus.downloaded_bytes,
                total_units: provisionStatus.total_units,
                unit: 'bytes',
                stage_eta_seconds: provisionStatus.eta_seconds,
                heartbeat_at: provisionStatus.heartbeat_at,
              }"
              :status="
                ['downloading', 'extracting', 'extracting_ffmpeg'].includes(provisionStatus.status)
                  ? 'running'
                  : provisionStatus.status
              "
            />
          </div>

          <div class="progress-meta">
            <span class="current-item">{{ provisionStatus.item || 'Iniciando download...' }}</span>
            <span v-if="provisionStatus.total_bytes > 0" class="bytes-info">
              {{ (provisionStatus.downloaded_bytes / (1024 * 1024)).toFixed(1) }} MB /
              {{ (provisionStatus.total_bytes / (1024 * 1024)).toFixed(1) }} MB
              <span v-if="provisionStatus.speed_bps > 0">
                ({{ (provisionStatus.speed_bps / (1024 * 1024)).toFixed(1) }} MB/s)</span
              >
            </span>
          </div>
        </div>

        <div v-if="error" class="onboarding-error-banner">
          <AppIcon name="warning" size="sm" />
          <span>{{ error }}</span>
        </div>

        <div class="onboarding-actions secondary-actions">
          <button
            type="button"
            class="button secondary"
            data-action="cancel-provision"
            @click="cancelProvision"
          >
            <AppIcon name="close" size="sm" />
            <span>Cancelar</span>
          </button>
        </div>
      </section>

      <!-- Step 3: Finished & API Key Handoff -->
      <section v-else-if="step === 'apikey'" class="onboarding-step">
        <div class="success-banner">
          <AppIcon name="check-circle" size="lg" class="success-icon" />
          <h3>Recursos locais preparados</h3>
          <p>
            Configure o provedor de IA para analisar a transcrição. Essa etapa utiliza a internet,
            envia somente texto e pode gerar custos. As chaves são armazenadas separadamente das
            preferências do projeto.
          </p>
        </div>

        <div class="api-key-card">
          <div class="provider-pills">
            <button
              type="button"
              class="pill-btn"
              :class="{ active: apiKeyProvider === 'gemini' }"
              :aria-pressed="apiKeyProvider === 'gemini'"
              :disabled="busy"
              @click="apiKeyProvider = 'gemini'"
            >
              Google Gemini
            </button>
            <button
              type="button"
              class="pill-btn"
              :class="{ active: apiKeyProvider === 'openrouter' }"
              :aria-pressed="apiKeyProvider === 'openrouter'"
              :disabled="busy"
              @click="apiKeyProvider = 'openrouter'"
            >
              OpenRouter
            </button>
          </div>

          <div class="key-field">
            <label class="diag-label">
              {{
                apiKeyProvider === 'gemini'
                  ? 'Chave de API do Google Gemini (Google AI Studio)'
                  : 'Chave de API do OpenRouter'
              }}
            </label>
            <div class="input-with-button">
              <input
                v-model="apiKeyInput"
                :disabled="busy"
                type="password"
                class="key-text-input"
                autocomplete="new-password"
                spellcheck="false"
                autocapitalize="off"
                data-1p-ignore
                aria-label="Chave de API"
                :placeholder="apiKeyProvider === 'gemini' ? 'AIzaSy...' : 'sk-or-v1-...'"
              />
              <button
                type="button"
                class="button primary"
                :disabled="busy || !apiKeyInput.trim()"
                @click="handleSaveKey"
              >
                <AppIcon name="key" size="sm" />
                <span>{{ busy ? 'Salvando…' : 'Salvar chave' }}</span>
              </button>
            </div>
          </div>

          <p v-if="keySaved" class="success-pill-msg">
            <AppIcon name="check" size="sm" /> Chave salva. Confira a conexão em Configurações antes
            de iniciar a análise.
          </p>
          <p v-if="error" role="alert" class="onboarding-error-banner">{{ error }}</p>
        </div>

        <div class="onboarding-actions">
          <button
            type="button"
            class="button primary large full-width"
            data-action="finish-onboarding"
            :disabled="busy"
            @click="finish"
          >
            <AppIcon name="check" size="md" />
            <span>Abrir AutoClip e Começar</span>
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.onboarding-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.onboarding-container {
  outline: none;
  max-height: calc(100dvh - 32px);
  overflow-y: auto;
  min-height: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
  width: 100%;
  max-width: 680px;
  box-shadow: var(--shadow-floating);
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  color: var(--color-text-primary);
}

.onboarding-header {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.header-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: var(--font-size-meta);
  font-weight: 600;
  color: var(--color-action-primary);
  background: var(--color-surface-selected);
  border: 1px solid var(--color-surface-selected);
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  width: fit-content;
}

.onboarding-header h2 {
  font-size: var(--font-size-title);
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
}

.header-subtitle {
  font-size: 0.88rem;
  color: var(--color-text-secondary);
  line-height: 1.45;
  margin: 0;
}

.onboarding-step {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.hardware-diagnosis-card {
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.diagnosis-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--color-text-primary);
  font-size: var(--font-size-body);
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border-subtle);
}

.diagnosis-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px 24px;
}

.diag-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.diag-label {
  font-size: var(--font-size-meta);
  color: var(--color-text-secondary);
  letter-spacing: 0.01em;
}

.diag-val {
  font-size: var(--font-size-body);
  line-height: 1.45;
  overflow-wrap: anywhere;
  font-weight: 500;
  color: var(--color-text-primary);
}

.tiers-selection-section {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.section-heading {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  font-size: 0.88rem;
}

.section-heading .hint {
  font-size: var(--font-size-meta);
  color: var(--color-text-secondary);
}

.tiers-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.65rem;
}

.tier-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-control);
  padding: 0.85rem 1.1rem;
  text-align: left;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  transition: all 0.2s ease;
  color: inherit;
}

.tier-card:hover {
  background: var(--color-surface-hover);
  border-color: var(--color-border-strong);
}

.tier-card.selected {
  background: var(--color-surface-selected);
  border-color: var(--color-action-primary);
}

.tier-card.recommended {
  border-color: var(--color-warning-surface);
}

.tier-card.selected.recommended {
  border-color: var(--color-action-primary);
}

.tier-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tier-title {
  font-weight: 600;
  font-size: 0.92rem;
  color: var(--color-text-primary);
}

.rec-pill {
  font-size: var(--font-size-meta);
  font-weight: 600;
  color: var(--color-warning-text);
  background: var(--color-warning-surface);
  border: 1px solid var(--color-warning-surface);
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
}

.tier-desc {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.35;
}

.speed-tag {
  font-size: var(--font-size-meta);
  color: var(--color-success-text);
  font-weight: 500;
}

.ffmpeg-option-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-control);
  padding: 0.85rem 1.1rem;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  cursor: pointer;
}

.checkbox-label input[type='checkbox'] {
  margin-top: 0.2rem;
  accent-color: var(--color-action-primary);
  cursor: pointer;
}

.checkbox-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.checkbox-info strong {
  font-size: 0.88rem;
  color: var(--color-text-primary);
}

.checkbox-info span {
  font-size: var(--font-size-meta);
  color: var(--color-text-secondary);
  line-height: 1.35;
}

.onboarding-error-banner {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--color-danger-soft);
  border: 1px solid var(--color-danger-soft);
  color: var(--color-error);
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.82rem;
}

.download-progress-card {
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.progress-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.spinner-item {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  color: var(--color-text-primary);
  font-size: 0.95rem;
}

.percent-badge {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--color-action-primary);
}

.progress-bar-track {
  width: 100%;
  height: 10px;
  background: var(--color-surface-hover);
  border-radius: 999px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: var(--color-action-primary);
  border-radius: 999px;
  transition: width 0.3s ease;
}

.progress-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}

.success-banner {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.65rem;
  padding: 1rem 0;
}

.success-icon {
  color: var(--color-success-text);
}

.success-banner h3 {
  margin: 0;
  font-size: 1.25rem;
  color: var(--color-text-primary);
}

.success-banner p {
  margin: 0;
  font-size: 0.86rem;
  color: var(--color-text-secondary);
  max-width: 520px;
  line-height: 1.45;
}

.api-key-card {
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-panel);
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.provider-pills {
  display: flex;
  gap: 0.5rem;
}

.pill-btn {
  background: var(--color-surface);
  border: 1px solid var(--color-border-subtle);
  color: var(--color-text-secondary);
  padding: 0.35rem 0.85rem;
  border-radius: 6px;
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pill-btn.active {
  background: var(--color-surface-selected);
  border-color: var(--color-action-primary);
  color: var(--color-text-primary);
  font-weight: 600;
}

.key-field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.input-with-button {
  display: flex;
  gap: 0.5rem;
}

.key-text-input {
  flex: 1;
  background: var(--color-canvas);
  border: 1px solid var(--color-border-control);
  border-radius: 6px;
  color: var(--color-text-primary);
  padding: 0.5rem 0.85rem;
  font-size: 0.88rem;
  font-family: monospace;
}

.key-text-input:focus {
  outline: none;
  border-color: var(--color-action-primary);
}

.success-pill-msg {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
  color: var(--color-success-text);
  margin: 0;
}

.onboarding-actions {
  display: flex;
  align-items: center;
}

.full-width {
  width: 100%;
  justify-content: center;
  padding: 0.75rem 1.25rem;
  font-size: 0.95rem;
  font-weight: 600;
}

.secondary-actions {
  justify-content: flex-end;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
