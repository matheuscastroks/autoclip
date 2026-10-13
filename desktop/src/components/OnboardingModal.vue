<script setup lang="ts">
import {ref,computed,onMounted,onUnmounted} from 'vue'
import {Cpu,HardDrive,Sparkles,Check,CheckCircle2,AlertTriangle,LoaderCircle,Download,X,KeyRound} from '@lucide/vue'
import type {HardwareProfile,ProvisionStatus} from '../types'
import {api} from '../api'

const props = defineProps<{
  profile: HardwareProfile | null
  toolsMissing: boolean
  asrMissing: boolean
  geminiKeyConfigured?: boolean
  openrouterKeyConfigured?: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'configured'): void
  (e: 'saveKey', key: string): void
  (e: 'saveOpenRouterKey', key: string): void
}>()

const step = ref<'diagnosis' | 'downloading' | 'apikey'>('diagnosis')
const selectedTier = ref<number>(props.profile?.recommended_tier || 2)
const installFfmpeg = ref<boolean>(props.toolsMissing)
const busy = ref<boolean>(false)
const error = ref<string | null>(null)

const apiKeyProvider = ref<'gemini' | 'openrouter'>('gemini')
const apiKeyInput = ref<string>('')
const keySaved = ref<boolean>(false)

const tiers = [
  {
    tier: 1,
    id: 'Systran/faster-whisper-base',
    title: 'Tier 1 (Leve)',
    desc: 'Whisper Base · ~140 MB · Baixo consumo de RAM e CPU',
    speed: 'Ultrarrápido'
  },
  {
    tier: 2,
    id: 'Systran/faster-whisper-small',
    title: 'Tier 2 (Equilibrado)',
    desc: 'Whisper Small · ~460 MB · Equilíbrio ideal de precisão e velocidade',
    speed: 'Padrão'
  },
  {
    tier: 3,
    id: 'Systran/faster-whisper-large-v3-turbo',
    title: 'Tier 3 (Alta Performance)',
    desc: 'Whisper Large v3 Turbo · ~800 MB · Fidelidade máxima em português',
    speed: 'Máxima Precisão'
  }
]

const selectedModelId = computed(() => {
  const t = tiers.find(item => item.tier === selectedTier.value)
  return t ? t.id : 'Systran/faster-whisper-small'
})

const provisionStatus = ref<ProvisionStatus>({
  status: 'idle',
  stage: 'idle',
  item: '',
  downloaded_bytes: 0,
  total_bytes: 0,
  speed_bps: 0,
  percent: 0,
  error: null
})

let pollTimer: ReturnType<typeof setInterval> | null = null

async function pollStatus() {
  try {
    const st = await api.provisionStatus()
    provisionStatus.value = st
    if (st.status === 'ready') {
      stopPolling()
      step.value = 'apikey'
      emit('configured')
    } else if (st.status === 'failed' || st.status === 'cancelled') {
      stopPolling()
      error.value = st.error || 'A instalação foi interrompida.'
    }
  } catch (e) {
    // keep polling
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(pollStatus, 800)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

async function startProvision() {
  busy.value = true
  error.value = null
  step.value = 'downloading'
  try {
    await api.provision({
      model_id: selectedModelId.value,
      install_ffmpeg: installFfmpeg.value
    })
    startPolling()
  } catch (e) {
    error.value = (e as Error).message
    step.value = 'diagnosis'
  } finally {
    busy.value = false
  }
}

async function cancelProvision() {
  try {
    await api.cancelProvision()
    stopPolling()
    step.value = 'diagnosis'
  } catch {}
}

async function handleSaveKey() {
  if (!apiKeyInput.value.trim()) return
  busy.value = true
  error.value = null
  try {
    if (apiKeyProvider.value === 'gemini') {
      emit('saveKey', apiKeyInput.value.trim())
    } else {
      emit('saveOpenRouterKey', apiKeyInput.value.trim())
    }
    keySaved.value = true
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    busy.value = false
  }
}

function finish() {
  emit('close')
}

onMounted(() => {
  if (props.profile) {
    selectedTier.value = props.profile.recommended_tier
  }
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div class="onboarding-overlay" role="dialog" aria-modal="true">
    <div class="onboarding-container">
      <header class="onboarding-header">
        <div class="header-badge">
          <Sparkles :size="18"/>
          <span>Instalação Zero-Config</span>
        </div>
        <h2>Configuração Inicial do AutoClip</h2>
        <p class="header-subtitle">
          Configuramos as ferramentas multimídia e o modelo Whisper diretamente no seu computador para garantir edição de cortes 100% offline.
        </p>
      </header>

      <!-- Step 1: Diagnosis & Model Selection -->
      <section v-if="step === 'diagnosis'" class="onboarding-step">
        <div v-if="profile" class="hardware-diagnosis-card">
          <div class="diagnosis-header">
            <Cpu :size="17"/>
            <strong>Diagnóstico de Hardware</strong>
          </div>
          <div class="diagnosis-grid">
            <div class="diag-item">
              <span class="diag-label">Processador (CPU)</span>
              <span class="diag-val">{{ profile.cpu_physical_cores }} núcleos físicos ({{ profile.cpu_logical_cores }} threads)</span>
            </div>
            <div class="diag-item">
              <span class="diag-label">Memória RAM</span>
              <span class="diag-val">{{ profile.ram_total_gb }} GB ({{ profile.ram_available_gb }} GB livres)</span>
            </div>
            <div class="diag-item">
              <span class="diag-label">Aceleração Gráfica (GPU)</span>
              <span class="diag-val">{{ profile.gpu_name ? profile.gpu_name + ' (' + profile.vram_gb + ' GB VRAM)' : (profile.has_cuda ? 'GPU NVIDIA CUDA detectada' : 'Modo CPU otimizado') }}</span>
            </div>
          </div>
        </div>

        <div class="tiers-selection-section">
          <div class="section-heading">
            <strong>Escolha o modelo de transcrição Whisper:</strong>
            <span class="hint">O tier recomendado foi pré-selecionado de acordo com seu hardware.</span>
          </div>

          <div class="tiers-grid">
            <button
              v-for="item in tiers"
              :key="item.tier"
              type="button"
              class="tier-card"
              :data-tier="item.tier"
              :class="{
                selected: selectedTier === item.tier,
                recommended: profile && profile.recommended_tier === item.tier
              }"
              @click="selectedTier = item.tier"
            >
              <div class="tier-top">
                <span class="tier-title">{{ item.title }}</span>
                <span v-if="profile && profile.recommended_tier === item.tier" class="rec-pill">
                  ⭐ Recomendado
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
            <input
              type="checkbox"
              v-model="installFfmpeg"
              data-action="toggle-ffmpeg"
            />
            <div class="checkbox-info">
              <strong>Instalar ferramentas multimídia FFmpeg & ffprobe</strong>
              <span>Baixa automaticamente a distribuição oficial Gyan FFmpeg para processar vídeos e extrair áudio com alta fidelidade.</span>
            </div>
          </label>
        </div>

        <div v-if="error" class="onboarding-error-banner">
          <AlertTriangle :size="16"/>
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
            <Download :size="17"/>
            <span>Instalar Dependências Automaticamente</span>
          </button>
        </div>
      </section>

      <!-- Step 2: Live Download Progress -->
      <section v-else-if="step === 'downloading'" class="onboarding-step">
        <div class="download-progress-card">
          <div class="progress-header">
            <div class="spinner-item">
              <LoaderCircle class="animate-spin" :size="20"/>
              <strong>Baixando e configurando dependências...</strong>
            </div>
            <span class="percent-badge">{{ provisionStatus.percent }}%</span>
          </div>

          <div class="progress-bar-track">
            <div class="progress-bar-fill" :style="{ width: provisionStatus.percent + '%' }"></div>
          </div>

          <div class="progress-meta">
            <span class="current-item">{{ provisionStatus.item || 'Iniciando download...' }}</span>
            <span v-if="provisionStatus.total_bytes > 0" class="bytes-info">
              {{ (provisionStatus.downloaded_bytes / (1024 * 1024)).toFixed(1) }} MB / {{ (provisionStatus.total_bytes / (1024 * 1024)).toFixed(1) }} MB
              <span v-if="provisionStatus.speed_bps > 0"> ({{ (provisionStatus.speed_bps / (1024 * 1024)).toFixed(1) }} MB/s)</span>
            </span>
          </div>
        </div>

        <div v-if="error" class="onboarding-error-banner">
          <AlertTriangle :size="16"/>
          <span>{{ error }}</span>
        </div>

        <div class="onboarding-actions secondary-actions">
          <button
            type="button"
            class="button secondary"
            data-action="cancel-provision"
            @click="cancelProvision"
          >
            <X :size="15"/>
            <span>Cancelar</span>
          </button>
        </div>
      </section>

      <!-- Step 3: Finished & API Key Handoff -->
      <section v-else-if="step === 'apikey'" class="onboarding-step">
        <div class="success-banner">
          <CheckCircle2 :size="32" class="success-icon"/>
          <h3>Dependências instaladas com sucesso!</h3>
          <p>
            Seu computador agora possui o Whisper e o FFmpeg operando 100% offline. Para habilitar a curadoria inteligente e seleção de momentos pelo AI Studio, configure sua chave de API abaixo:
          </p>
        </div>

        <div class="api-key-card">
          <div class="provider-pills">
            <button
              type="button"
              class="pill-btn"
              :class="{active: apiKeyProvider === 'gemini'}"
              @click="apiKeyProvider = 'gemini'"
            >
              Google Gemini
            </button>
            <button
              type="button"
              class="pill-btn"
              :class="{active: apiKeyProvider === 'openrouter'}"
              @click="apiKeyProvider = 'openrouter'"
            >
              OpenRouter
            </button>
          </div>

          <div class="key-field">
            <label class="diag-label">
              {{ apiKeyProvider === 'gemini' ? 'Chave de API do Google Gemini (Google AI Studio)' : 'Chave de API do OpenRouter' }}
            </label>
            <div class="input-with-button">
              <input
                type="password"
                v-model="apiKeyInput"
                class="key-text-input"
                :placeholder="apiKeyProvider === 'gemini' ? 'AIzaSy...' : 'sk-or-v1-...'"
              />
              <button
                type="button"
                class="button primary"
                :disabled="busy || !apiKeyInput.trim()"
                @click="handleSaveKey"
              >
                <KeyRound :size="15"/>
                <span>Salvar Chave</span>
              </button>
            </div>
          </div>

          <p v-if="keySaved" class="success-pill-msg">
            <Check :size="14"/> Chave de API validada e configurada com sucesso!
          </p>
        </div>

        <div class="onboarding-actions">
          <button
            type="button"
            class="button primary large full-width"
            data-action="finish-onboarding"
            @click="finish"
          >
            <Check :size="17"/>
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
  backdrop-filter: blur(8px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
}

.onboarding-container {
  background: #11141a;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 14px;
  width: 100%;
  max-width: 680px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.8);
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  color: #e4e7eb;
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
  font-size: 0.78rem;
  font-weight: 600;
  color: #79c0ff;
  background: rgba(56, 139, 253, 0.12);
  border: 1px solid rgba(56, 139, 253, 0.3);
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  width: fit-content;
}

.onboarding-header h2 {
  font-size: 1.45rem;
  font-weight: 700;
  color: #ffffff;
  margin: 0;
}

.header-subtitle {
  font-size: 0.88rem;
  color: #8b949e;
  line-height: 1.45;
  margin: 0;
}

.onboarding-step {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.hardware-diagnosis-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.diagnosis-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #a5d6ff;
  font-size: 0.88rem;
}

.diagnosis-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
}

.diag-item {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.diag-label {
  font-size: 0.75rem;
  color: #8b949e;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.diag-val {
  font-size: 0.85rem;
  font-weight: 500;
  color: #c9d1d9;
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
  font-size: 0.78rem;
  color: #8b949e;
}

.tiers-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.65rem;
}

.tier-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
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
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.18);
}

.tier-card.selected {
  background: rgba(56, 139, 253, 0.08);
  border-color: #388bfd;
  box-shadow: 0 0 12px rgba(56, 139, 253, 0.2);
}

.tier-card.recommended {
  border-color: rgba(210, 153, 34, 0.5);
}

.tier-card.selected.recommended {
  border-color: #388bfd;
}

.tier-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tier-title {
  font-weight: 600;
  font-size: 0.92rem;
  color: #ffffff;
}

.rec-pill {
  font-size: 0.72rem;
  font-weight: 600;
  color: #d29922;
  background: rgba(210, 153, 34, 0.12);
  border: 1px solid rgba(210, 153, 34, 0.4);
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
}

.tier-desc {
  font-size: 0.8rem;
  color: #8b949e;
  margin: 0;
  line-height: 1.35;
}

.speed-tag {
  font-size: 0.72rem;
  color: #7ee787;
  font-weight: 500;
}

.ffmpeg-option-card {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 0.85rem 1.1rem;
}

.checkbox-label {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  margin-top: 0.2rem;
  accent-color: #388bfd;
  cursor: pointer;
}

.checkbox-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.checkbox-info strong {
  font-size: 0.88rem;
  color: #e6edf3;
}

.checkbox-info span {
  font-size: 0.78rem;
  color: #8b949e;
  line-height: 1.35;
}

.onboarding-error-banner {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(248, 81, 73, 0.12);
  border: 1px solid rgba(248, 81, 73, 0.4);
  color: #f85149;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.82rem;
}

.download-progress-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
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
  color: #ffffff;
  font-size: 0.95rem;
}

.percent-badge {
  font-size: 1.15rem;
  font-weight: 700;
  color: #388bfd;
}

.progress-bar-track {
  width: 100%;
  height: 10px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 999px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #388bfd, #58a6ff);
  border-radius: 999px;
  transition: width 0.3s ease;
}

.progress-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #8b949e;
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
  color: #2ea043;
}

.success-banner h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #ffffff;
}

.success-banner p {
  margin: 0;
  font-size: 0.86rem;
  color: #8b949e;
  max-width: 520px;
  line-height: 1.45;
}

.api-key-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
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
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #8b949e;
  padding: 0.35rem 0.85rem;
  border-radius: 6px;
  font-size: 0.82rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pill-btn.active {
  background: rgba(56, 139, 253, 0.15);
  border-color: #388bfd;
  color: #ffffff;
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
  background: #0d1117;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 6px;
  color: #ffffff;
  padding: 0.5rem 0.85rem;
  font-size: 0.88rem;
  font-family: monospace;
}

.key-text-input:focus {
  outline: none;
  border-color: #388bfd;
}

.success-pill-msg {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
  color: #2ea043;
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
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
