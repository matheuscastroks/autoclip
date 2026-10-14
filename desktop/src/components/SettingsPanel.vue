<script setup lang="ts">
import AppButton from './AppButton.vue';
import AppSelect from './AppSelect.vue';
import { reactive, ref, watch, computed, onMounted, nextTick } from 'vue';
import {
  FolderOpen,
  KeyRound,
  Monitor,
  Save,
  Cpu,
  Sparkles,
  Scissors,
  CheckCircle2,
  AlertCircle,
  ChevronRight,
  ChevronLeft,
  HardDrive,
  Sliders,
} from '@lucide/vue';
import { notify } from '../notifications';
import type { Config, GeminiConnection } from '../types';

const props = defineProps<{
  config: Config;
  saveConfig: (value: Config) => Promise<unknown>;
  saveKey: (value: string) => Promise<unknown>;
  saveOpenRouterKey?: (value: string) => Promise<unknown>;
  saveOpenrouterKey?: (value: string) => Promise<unknown>;
  pick: (kind: string) => Promise<string | null>;
  getConnection?: () => Promise<GeminiConnection>;
  testConnection?: () => Promise<GeminiConnection>;
}>();

const values = reactive({
  clip_preferred_seconds: 180,
  clip_max_seconds: 300,
  pause_mode: 'conservative' as const,
  show_thought_summaries: true,
  ai_provider: 'gemini' as 'gemini' | 'openrouter',
  openrouter_model: 'openrouter/free',
  openrouter_key_configured: props.config.openrouter_key_configured,
  ...props.config,
});

const key = ref(''),
  openrouterKey = ref(''),
  busy = ref(false);
const settingsStep = ref(0);

const settingsCategories = [
  { num: '01', title: 'Recursos locais', sub: 'Whisper, FFmpeg e hardware local', icon: Cpu },
  { num: '02', title: 'IA e modelos', sub: 'Gemini, OpenRouter e chaves de API', icon: Sparkles },
  { num: '03', title: 'Duração dos cortes', sub: 'Tempo alvo e limite máximo', icon: Scissors },
];
const settingsLabels = ['Recursos locais', 'IA e modelos', 'Duração dos cortes'];

let invalidHandled = false;
function invalidSetting(event: Event) {
  event.preventDefault();
  if (invalidHandled) return;
  invalidHandled = true;
  const target = event.target as HTMLElement;
  const section = target.closest<HTMLElement>('[data-settings-step]');
  if (section) settingsStep.value = Number(section.dataset.settingsStep);
  for (
    let details = target.closest('details');
    details;
    details = details.parentElement?.closest('details') || null
  )
    details.open = true;
  notify.error('Confira os campos destacados desta etapa antes de salvar.');
  void nextTick(() => {
    target.focus();
    invalidHandled = false;
  });
}

function settingsKey(e: KeyboardEvent) {
  const k = e.key;
  let n = settingsStep.value;
  if (k === 'ArrowRight' || k === 'ArrowDown') n = (n + 1) % 3;
  else if (k === 'ArrowLeft' || k === 'ArrowUp') n = (n + 2) % 3;
  else if (k === 'Home') n = 0;
  else if (k === 'End') n = 2;
  else return;
  e.preventDefault();
  settingsStep.value = n;
  (e.currentTarget as HTMLElement).querySelectorAll<HTMLButtonElement>('button')[n]?.focus();
}

const connection = ref<GeminiConnection | null>(null),
  validating = ref(false);
const statusLabel = computed(() =>
  validating.value
    ? 'Validando…'
    : connection.value?.status === 'valid'
      ? 'Conexão validada'
      : connection.value?.status === 'invalid'
        ? 'Chave sem acesso'
        : connection.value?.status === 'unavailable'
          ? 'Conexão indisponível'
          : props.config.gemini_key_configured
            ? 'Chave salva · não testada'
            : 'Chave não configurada'
);
const openrouterStatusLabel = computed(() =>
  values.openrouter_key_configured || props.config.openrouter_key_configured
    ? 'Chave configurada'
    : 'Chave não configurada'
);

const freeModels = [
  {
    id: 'openrouter/free',
    name: 'openrouter/free',
    desc: 'Automático gratuito (melhor disponível)',
  },
  {
    id: 'meta-llama/llama-3.3-70b-instruct:free',
    name: 'Llama 3.3 70B',
    desc: 'meta-llama/llama-3.3-70b-instruct:free',
  },
  { id: 'google/gemma-3-27b-it:free', name: 'Gemma 3 27B', desc: 'google/gemma-3-27b-it:free' },
  { id: 'deepseek/deepseek-chat', name: 'DeepSeek V3', desc: 'deepseek/deepseek-chat (pago)' },
];

const models = computed(() => connection.value?.models || []);
const modelOptions = computed(() => [
  ...(!models.value.some(m => m.id === values.gemini_model)
    ? [
        {
          value: values.gemini_model,
          label:
            values.gemini_model +
            ' — ' +
            (connection.value?.status === 'valid' ? 'não aparece no catálogo' : 'modelo salvo'),
          disabled: true,
        },
      ]
    : []),
  ...models.value.map(m => ({ value: m.id, label: m.display_name + ' · ' + m.id })),
]);
const listed = computed(() => models.value.some(m => m.id === values.gemini_model));
const missingModel = computed(
  () =>
    values.ai_provider === 'gemini' &&
    connection.value?.status === 'valid' &&
    models.value.length > 0 &&
    !listed.value
);

watch(
  () => props.config,
  (value, old) => {
    for (const field of Object.keys(value) as (keyof Config)[]) {
      if (value[field] !== old[field]) Object.assign(values, { [field]: value[field] });
    }
    if (value.openrouter_key_configured !== undefined)
      values.openrouter_key_configured = value.openrouter_key_configured;
  },
  { deep: true }
);

onMounted(async () => {
  if (props.getConnection)
    try {
      connection.value = await props.getConnection();
    } catch (e) {
      notify.error((e as Error).message);
    }
});

async function execute(fn: () => Promise<unknown>, success: string) {
  busy.value = true;
  try {
    await fn();
    if (success) notify.success(success);
  } catch (e) {
    notify.error((e as Error).message);
  } finally {
    busy.value = false;
  }
}

async function saveKey() {
  validating.value = true;
  await execute(async () => {
    const result = await props.saveKey(key.value.trim());
    if (result) connection.value = result as GeminiConnection;
    key.value = '';
    if (!result || connection.value?.status === 'valid')
      notify.success(
        result ? 'Conexão validada. Chave armazenada no Windows.' : 'Chave armazenada no Windows.'
      );
    else notify.error(connection.value?.message || 'Não foi possível validar a conexão.');
  }, '');
  validating.value = false;
}

async function saveOpenRouterKey() {
  const saveFn = props.saveOpenRouterKey || props.saveOpenrouterKey;
  if (!saveFn) {
    notify.error('Função para salvar chave OpenRouter não está disponível.');
    return;
  }
  validating.value = true;
  await execute(async () => {
    await saveFn(openrouterKey.value.trim());
    openrouterKey.value = '';
    values.openrouter_key_configured = true;
    if (props.config) props.config.openrouter_key_configured = true;
    notify.success('Chave OpenRouter armazenada no Windows com segurança.');
  }, '');
  validating.value = false;
}

async function testConnection() {
  if (!props.testConnection) return;
  validating.value = true;
  await execute(async () => {
    connection.value = await props.testConnection!();
    if (connection.value.status === 'valid')
      notify.success('Conexão Gemini validada. Catálogo atualizado.');
    else notify.error(connection.value.message);
  }, '');
  validating.value = false;
}

async function saveSettings() {
  if (values.clip_preferred_seconds > values.clip_max_seconds) {
    notify.error('A duração preferida deve ser menor ou igual à máxima.');
    return;
  }
  if (values.ai_provider === 'openrouter' && !values.openrouter_model?.trim()) {
    notify.error('Informe um modelo do OpenRouter.');
    return;
  }
  if (values.ai_provider === 'gemini' && missingModel.value) {
    notify.warning('Selecione um modelo Gemini disponível no catálogo antes de salvar.');
    return;
  }
  await execute(() => props.saveConfig({ ...values }), 'Configurações salvas.');
}

async function pick(kind: string, field: 'asr_model_path' | 'ffmpeg' | 'ffprobe') {
  await execute(async () => {
    const result = await props.pick(kind);
    if (result) values[field] = result;
  }, '');
}
</script>

<template>
  <div class="settings-workspace">
    <header class="page-heading">
      <div>
        <p class="breadcrumb">Preferências do aplicativo</p>
        <h1>Configurações</h1>
        <p>Ajuste os motores de IA, aceleração local de hardware e regras editoriais de cortes.</p>
      </div>
    </header>

    <div class="settings-hub-layout">
      <!-- Coluna esquerda: Menu Vertical de Categorias -->
      <aside class="settings-nav-sidebar">
        <nav
          class="settings-tiles"
          role="tablist"
          aria-label="Etapas de configuração"
          @keydown="settingsKey"
        >
          <AppButton
            v-for="(cat, index) in settingsCategories"
            :key="cat.title"
            role="tab"
            :id="'settings-tab-' + index"
            :aria-selected="settingsStep === index"
            aria-controls="settings-content"
            :tabindex="settingsStep === index ? 0 : -1"
            class="settings-category-btn"
            :class="{ selected: settingsStep === index }"
            @click="settingsStep = index"
          >
            <span class="cat-num">{{ cat.num }}</span>
            <div class="cat-content">
              <span class="cat-title">{{ cat.title }}</span>
              <span class="cat-sub">{{ cat.sub }}</span>
            </div>
            <div
              class="cat-indicator"
              :class="
                index === 0
                  ? config.asr_available && config.tools_available
                    ? 'ready'
                    : 'warn'
                  : index === 1
                    ? (
                        values.ai_provider === 'openrouter'
                          ? values.openrouter_key_configured || config.openrouter_key_configured
                          : config.gemini_key_configured
                      )
                      ? 'ready'
                      : 'warn'
                    : 'ready'
              "
            ></div>
          </AppButton>
        </nav>
      </aside>

      <!-- Coluna direita: Painel Principal do Formulário -->
      <main class="settings-content-pane">
        <form
          id="settings-content"
          role="tabpanel"
          :aria-labelledby="'settings-tab-' + settingsStep"
          class="settings-main"
          @submit.prevent="saveSettings"
          @invalid.capture="invalidSetting"
        >
          <!-- Etapa 0: Recursos Locais (Grid de 2 Colunas) -->
          <div
            v-show="settingsStep === 0"
            data-settings-step="0"
            class="step-grid-2col local-resources"
          >
            <!-- Coluna 1: Diagnóstico e Ambiente Local -->
            <section class="setting-section">
              <div class="section-title-wrap">
                <div class="section-icon"><Cpu :size="20" /></div>
                <div>
                  <h2>Diagnóstico do ambiente</h2>
                  <p>Processamento 100% local em CPU. Sem dependência de nuvem para mídia.</p>
                </div>
              </div>

              <div class="readiness-banner-vertical">
                <div class="readiness-card" :class="{ ok: config.asr_available }">
                  <div class="readiness-card-icon">
                    <CheckCircle2 v-if="config.asr_available" :size="20" />
                    <AlertCircle v-else :size="20" />
                  </div>
                  <div class="readiness-card-info">
                    <strong>Whisper (Transcrição de Áudio)</strong>
                    <span>{{
                      config.asr_available
                        ? 'Modelo local encontrado e pronto para uso'
                        : 'Modelo local não encontrado no diretório'
                    }}</span>
                  </div>
                </div>

                <div class="readiness-card" :class="{ ok: config.tools_available }">
                  <div class="readiness-card-icon">
                    <CheckCircle2 v-if="config.tools_available" :size="20" />
                    <AlertCircle v-else :size="20" />
                  </div>
                  <div class="readiness-card-info">
                    <strong>FFmpeg & ffprobe (Corte e Renderização)</strong>
                    <span>{{
                      config.tools_available
                        ? 'Ferramentas multimídia detectadas e operacionais'
                        : 'Executáveis não encontrados nos caminhos informados'
                    }}</span>
                  </div>
                </div>
              </div>
            </section>

            <!-- Coluna 2: Caminhos dos Executáveis e Modelos -->
            <section class="setting-section">
              <div class="section-title-wrap">
                <div class="section-icon"><FolderOpen :size="20" /></div>
                <div>
                  <h2>Caminhos e executáveis</h2>
                  <p>Aponte as pastas dos modelos e ferramentas no disco.</p>
                </div>
              </div>

              <div class="fields-stack">
                <label class="field">
                  Pasta do modelo Whisper
                  <span class="input-action">
                    <input
                      v-model="values.asr_model_path"
                      required
                      placeholder="Caminho para o diretório do modelo Whisper..."
                    />
                    <el-tooltip content="Escolher pasta do modelo Whisper" placement="top">
                      <AppButton
                        type="button"
                        class="icon-button"
                        title="Escolher pasta do modelo"
                        @click="pick('model', 'asr_model_path')"
                        ><FolderOpen :size="18"
                      /></AppButton>
                    </el-tooltip>
                  </span>
                  <small>Modelo multilíngue com suporte ao português (whisper-small).</small>
                </label>

                <label class="field">
                  Executável FFmpeg
                  <span class="input-action">
                    <input
                      v-model="values.ffmpeg"
                      required
                      placeholder="Caminho para ffmpeg.exe..."
                    />
                    <el-tooltip content="Localizar executável do FFmpeg" placement="top">
                      <AppButton
                        type="button"
                        class="icon-button"
                        title="Localizar FFmpeg"
                        @click="pick('ffmpeg', 'ffmpeg')"
                        ><FolderOpen :size="17"
                      /></AppButton>
                    </el-tooltip>
                  </span>
                  <small>Usado para extração de áudio, face-tracking e codificação de vídeo.</small>
                </label>

                <label class="field">
                  Executável ffprobe
                  <span class="input-action">
                    <input
                      v-model="values.ffprobe"
                      required
                      placeholder="Caminho para ffprobe.exe..."
                    />
                    <el-tooltip content="Localizar executável do ffprobe" placement="top">
                      <AppButton
                        type="button"
                        class="icon-button"
                        title="Localizar ffprobe"
                        @click="pick('ffprobe', 'ffprobe')"
                        ><FolderOpen :size="17"
                      /></AppButton>
                    </el-tooltip>
                  </span>
                  <small>Usado para inspeção técnica e validação dos streams de vídeo.</small>
                </label>
              </div>
            </section>
          </div>

          <!-- Etapa 1: IA & Provedor -->
          <div v-show="settingsStep === 1" data-settings-step="1" class="step-ia-wrap">
            <!-- Full Width: Seletor Visual de Provedor -->
            <section class="setting-section provider-selector-section">
              <div class="section-title-wrap">
                <div class="section-icon"><Sparkles :size="20" /></div>
                <div>
                  <h2>Provedor de inteligência artificial</h2>
                  <p>
                    Selecione o serviço de IA utilizado após a transcrição para analisar argumentos
                    e sugerir cortes.
                  </p>
                </div>
              </div>

              <div class="provider-switch-row">
                <label
                  class="provider-radio-card"
                  :class="{ selected: values.ai_provider === 'gemini' }"
                  @click="values.ai_provider = 'gemini'"
                >
                  <input
                    type="radio"
                    v-model="values.ai_provider"
                    value="gemini"
                    data-field="provider-gemini"
                    @change="values.ai_provider = 'gemini'"
                  />
                  <div class="provider-card-content">
                    <div class="provider-card-header">
                      <strong>Google Gemini</strong>
                      <el-tag
                        :type="config.gemini_key_configured ? 'success' : 'warning'"
                        size="small"
                        effect="dark"
                        class="badge"
                        :class="config.gemini_key_configured ? 'badge-ready' : 'badge-warn'"
                      >
                        {{ config.gemini_key_configured ? 'Chave pronta' : 'Sem chave' }}
                      </el-tag>
                    </div>
                    <small
                      >Gemini 2.5 Flash nativo com catálogo sincronizado e validação direta de
                      modelos da Google.</small
                    >
                  </div>
                </label>

                <label
                  class="provider-radio-card"
                  :class="{ selected: values.ai_provider === 'openrouter' }"
                  @click="values.ai_provider = 'openrouter'"
                >
                  <input
                    type="radio"
                    v-model="values.ai_provider"
                    value="openrouter"
                    data-field="provider-openrouter"
                    @change="values.ai_provider = 'openrouter'"
                  />
                  <div class="provider-card-content">
                    <div class="provider-card-header">
                      <strong>OpenRouter</strong>
                      <el-tag
                        :type="
                          values.openrouter_key_configured || config.openrouter_key_configured
                            ? 'success'
                            : 'warning'
                        "
                        size="small"
                        effect="dark"
                        class="badge"
                        :class="
                          values.openrouter_key_configured || config.openrouter_key_configured
                            ? 'badge-ready'
                            : 'badge-warn'
                        "
                      >
                        {{
                          values.openrouter_key_configured || config.openrouter_key_configured
                            ? 'Chave pronta'
                            : 'Sem chave'
                        }}
                      </el-tag>
                    </div>
                    <small
                      >Modelos gratuitos (:free) como Llama 3.3 70B, Gemma ou DeepSeek sem custos de
                      geração.</small
                    >
                  </div>
                </label>
              </div>
            </section>

            <!-- 2 Colunas Lado a Lado: Credencial (Esquerda) e Seleção de Modelo (Direita) -->
            <div class="provider-details-grid">
              <!-- PROVEDOR: GEMINI -->
              <template v-if="values.ai_provider === 'gemini'">
                <!-- Coluna 1: Credencial Gemini -->
                <section class="credential-panel">
                  <div class="section-title-wrap">
                    <div class="section-icon"><KeyRound :size="20" /></div>
                    <div class="title-with-pill">
                      <h2>Chave Gemini</h2>
                      <el-tag
                        size="small"
                        :type="
                          validating
                            ? 'warning'
                            : connection?.status === 'valid'
                              ? 'success'
                              : 'info'
                        "
                        effect="dark"
                        class="status-pill"
                        :data-status="
                          validating
                            ? 'running'
                            : connection?.status === 'valid'
                              ? 'completed'
                              : 'pending'
                        "
                      >
                        {{ statusLabel }}
                      </el-tag>
                    </div>
                  </div>

                  <p class="section-desc">
                    Armazenada no Gerenciador de Credenciais do Windows. O aplicativo não exibe a
                    chave salva.
                  </p>

                  <AppButton
                    v-if="connection?.status === 'invalid' || connection?.status === 'unavailable'"
                    type="button"
                    class="text-button"
                    @click="notify.error(connection!.message)"
                  >
                    Ver motivo da falha
                  </AppButton>

                  <label class="field">
                    {{ config.gemini_key_configured ? 'Substituir chave' : 'Adicionar chave' }}
                    <input
                      type="password"
                      @keydown.enter.prevent="!busy && key.trim() && saveKey()"
                      v-model="key"
                      autocomplete="new-password"
                      placeholder="Cole sua chave de API do Google Gemini..."
                    />
                  </label>

                  <div class="credential-buttons-row">
                    <AppButton
                      type="button"
                      class="button secondary"
                      data-action="save-key"
                      :disabled="busy || !key.trim()"
                      @click="saveKey"
                    >
                      <KeyRound :size="16" />{{ validating ? 'Validando…' : 'Salvar e validar' }}
                    </AppButton>
                    <AppButton
                      type="button"
                      class="button secondary"
                      data-action="test-gemini"
                      :disabled="busy || !config.gemini_key_configured"
                      @click="testConnection"
                    >
                      {{ validating ? 'Validando…' : 'Testar conexão / Catálogo' }}
                    </AppButton>
                  </div>

                  <p v-if="connection?.checked_at" class="test-timestamp">
                    Último teste: {{ new Date(connection.checked_at).toLocaleString('pt-BR') }}
                  </p>
                  <p class="api-cost-note">
                    O teste consulta apenas o catálogo. Não gera conteúdo nem consome cota de
                    geração.
                  </p>
                </section>

                <!-- Coluna 2: Seleção de Trechos / Modelo Gemini -->
                <section class="setting-section">
                  <div class="section-title-wrap">
                    <div class="section-icon"><Sparkles :size="20" /></div>
                    <div>
                      <h2>Seleção de trechos</h2>
                      <p>
                        Projetos novos seguem da transcrição para a análise com Gemini
                        automaticamente.
                      </p>
                    </div>
                  </div>

                  <label class="field">
                    Modelo Gemini
                    <AppSelect
                      v-model="values.gemini_model"
                      label="Modelo Gemini"
                      data-field="gemini-model"
                      :options="modelOptions"
                      required
                      :disabled="busy || !models.length"
                    />
                    <small v-if="missingModel" class="warning-text"
                      >O modelo salvo não aparece no catálogo. Escolha outro modelo
                      explicitamente.</small
                    >
                    <small v-else>{{
                      models.length
                        ? models.length + ' modelos disponíveis no catálogo.'
                        : 'Teste a conexão para carregar os modelos disponíveis.'
                    }}</small>
                  </label>
                </section>
              </template>

              <!-- PROVEDOR: OPENROUTER -->
              <template v-else-if="values.ai_provider === 'openrouter'">
                <!-- Coluna 1: Credencial OpenRouter -->
                <section class="credential-panel">
                  <div class="section-title-wrap">
                    <div class="section-icon"><KeyRound :size="20" /></div>
                    <div class="title-with-pill">
                      <h2>Chave OpenRouter</h2>
                      <el-tag
                        size="small"
                        :type="
                          values.openrouter_key_configured || config.openrouter_key_configured
                            ? 'success'
                            : 'info'
                        "
                        effect="dark"
                        class="status-pill"
                        :data-status="
                          values.openrouter_key_configured || config.openrouter_key_configured
                            ? 'completed'
                            : 'pending'
                        "
                      >
                        {{ openrouterStatusLabel }}
                      </el-tag>
                    </div>
                  </div>

                  <p class="section-desc">
                    Armazenada no Gerenciador de Credenciais do Windows. Obtenha sua chave em
                    <strong>openrouter.ai/keys</strong>.
                  </p>

                  <label class="field">
                    {{
                      values.openrouter_key_configured || config.openrouter_key_configured
                        ? 'Substituir chave OpenRouter'
                        : 'Adicionar chave OpenRouter'
                    }}
                    <input
                      type="password"
                      @keydown.enter.prevent="!busy && openrouterKey.trim() && saveOpenRouterKey()"
                      v-model="openrouterKey"
                      autocomplete="new-password"
                      placeholder="Cole sua chave sk-or-v1-..."
                    />
                  </label>

                  <div class="credential-buttons-row">
                    <AppButton
                      type="button"
                      class="button secondary"
                      data-action="save-openrouter-key"
                      :disabled="busy || !openrouterKey.trim()"
                      @click="saveOpenRouterKey"
                    >
                      <KeyRound :size="16" />{{
                        validating ? 'Salvando…' : 'Salvar chave OpenRouter'
                      }}
                    </AppButton>
                  </div>
                </section>

                <!-- Coluna 2: Modelo OpenRouter & Chips Rápidos -->
                <section class="setting-section">
                  <div class="section-title-wrap">
                    <div class="section-icon"><Sparkles :size="20" /></div>
                    <div>
                      <h2>Modelo OpenRouter</h2>
                      <p>
                        Selecione um modelo gratuito sugerido ou informe qualquer modelo do
                        catálogo.
                      </p>
                    </div>
                  </div>

                  <div class="quick-chips-wrap">
                    <span class="chips-label">Modelos populares gratuitos:</span>
                    <div class="quick-chips">
                      <button
                        v-for="m in freeModels"
                        :key="m.id"
                        type="button"
                        class="model-chip"
                        :class="{ active: values.openrouter_model === m.id }"
                        @click="values.openrouter_model = m.id"
                      >
                        <div class="chip-title-row">
                          <strong>{{ m.name }}</strong>
                          <el-tag
                            v-if="m.id.endsWith(':free')"
                            size="small"
                            type="success"
                            effect="plain"
                            class="chip-badge"
                            >Grátis</el-tag
                          >
                        </div>
                        <small>{{ m.desc }}</small>
                      </button>
                    </div>
                  </div>

                  <label class="field">
                    Identificador do modelo
                    <input
                      v-model="values.openrouter_model"
                      data-field="openrouter-model"
                      required
                      placeholder="Ex: openrouter/free, meta-llama/llama-3.3-70b-instruct:free..."
                    />
                    <small
                      >Você pode digitar qualquer modelo suportado pelo OpenRouter (ex:
                      <code>meta-llama/llama-3.3-70b-instruct:free</code>).</small
                    >
                  </label>
                </section>
              </template>
            </div>
          </div>

          <!-- Etapa 2: Duração dos Cortes -->
          <div v-show="settingsStep === 2" data-settings-step="2" class="step-cuts-wrap">
            <section class="setting-section cuts-duration-section">
              <div class="section-title-wrap">
                <div class="section-icon"><Scissors :size="20" /></div>
                <div>
                  <h2>Duração dos cortes</h2>
                  <p>
                    Mínimo de 1 minuto (60s) e máximo de 5 minutos (300s). Prioriza concluir o
                    argumento do orador.
                  </p>
                </div>
              </div>

              <div class="field-pair">
                <label class="field">
                  Duração preferida (segundos)
                  <input
                    type="number"
                    data-field="clip-preferred"
                    v-model.number="values.clip_preferred_seconds"
                    min="60"
                    max="300"
                    required
                  />
                  <small>Alvo recomendado (60 a 300 segundos).</small>
                </label>
                <label class="field">
                  Duração máxima (segundos)
                  <input
                    type="number"
                    data-field="clip-max"
                    v-model.number="values.clip_max_seconds"
                    min="60"
                    max="300"
                    required
                  />
                  <small>Limite máximo absoluto (60 a 300 segundos).</small>
                </label>
              </div>

              <div class="editorial-options">
                <label class="check-row">
                  <input
                    type="checkbox"
                    data-field="thought-summaries"
                    v-model="values.show_thought_summaries"
                  />
                  <span>Mostrar resumos de análise enviados pela IA</span>
                </label>
              </div>
            </section>
          </div>

          <!-- Barra Persistente de Ações -->
          <div class="setting-save">
            <AppButton
              type="submit"
              class="button primary"
              data-action="save-config"
              :disabled="busy || missingModel"
              @click="saveSettings"
            >
              <Save :size="16" />Salvar configurações
            </AppButton>
            <div class="actions">
              <AppButton
                v-if="settingsStep > 0"
                type="button"
                class="button secondary"
                @click="settingsStep--"
              >
                <ChevronLeft :size="15" />Anterior
              </AppButton>
              <AppButton
                v-if="settingsStep < 2"
                type="button"
                class="button secondary"
                @click="settingsStep++"
              >
                Próximo passo<ChevronRight :size="15" />
              </AppButton>
            </div>
          </div>
        </form>
      </main>
    </div>
  </div>
</template>

<style scoped>
.settings-workspace {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
}

.settings-hub-layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 24px;
  align-items: start;
  width: 100%;
}

.settings-nav-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: sticky;
  top: 20px;
}

.settings-tiles {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: var(--radius-panel, 14px);
  padding: 8px;
}

.settings-category-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  text-align: left;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--color-text-secondary, var(--muted));
  transition: all 0.15s ease;
  position: relative;
}

.settings-category-btn:hover {
  background: var(--color-surface-hover, var(--soft));
  color: var(--color-text-primary, var(--ink));
}

.settings-category-btn.selected {
  background: var(--color-accent-subtle, var(--accent-soft));
  border-color: var(--color-accent, #d97724);
  color: var(--color-accent-light, #f9a35c);
}

.cat-num {
  font-family: var(--font-mono, monospace);
  font-size: 0.85rem;
  font-weight: 700;
  opacity: 0.7;
}

.cat-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.cat-title {
  font-size: 0.88rem;
  font-weight: 600;
  line-height: 1.2;
}

.cat-sub {
  font-size: 0.73rem;
  opacity: 0.75;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cat-indicator {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}

.cat-indicator.ready {
  background: #10b981;
}

.cat-indicator.warn {
  background: #f59e0b;
}

.settings-content-pane {
  min-width: 0;
  width: 100%;
}

.settings-main {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--radius-panel, 14px);
  padding: 26px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  width: 100%;
}

/* Grids que aproveitam a largura de visualização */
.step-grid-2col {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
  width: 100%;
}

.step-ia-wrap {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
}

.step-cuts-wrap {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
}

.editorial-options {
  margin-top: 6px;
  padding-top: 14px;
  border-top: 1px solid var(--line);
}

.provider-details-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
  width: 100%;
  align-items: stretch;
}

.setting-section {
  background: var(--soft);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 22px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-sizing: border-box;
}

.credential-panel {
  background: var(--soft);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 22px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-sizing: border-box;
}

.fields-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-title-wrap {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 4px;
}

.section-icon {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  background: var(--color-surface, var(--panel));
  color: var(--color-accent-light, #f9a35c);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1px solid var(--color-border-subtle, var(--line));
}

.title-with-pill {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.section-title-wrap h2 {
  font-size: 1.05rem;
  font-weight: 600;
  margin: 0 0 3px;
  color: var(--color-text-primary, var(--ink));
}

.section-title-wrap p {
  margin: 0;
  font-size: 0.82rem;
  color: var(--color-text-muted, var(--muted));
  line-height: 1.4;
}

.section-desc {
  font-size: 0.8rem;
  color: var(--color-text-muted, var(--muted));
  margin: 0;
  line-height: 1.45;
}

/* Cards de Provedor */
.provider-switch-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.provider-radio-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px 18px;
  border-radius: 12px;
  border: 1px solid var(--color-border-subtle, var(--line));
  background: var(--color-surface, var(--panel));
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.provider-radio-card input[type='radio'] {
  margin-top: 3px;
  accent-color: var(--color-accent, #d97724);
}

.provider-radio-card:hover {
  border-color: var(--color-accent, #d97724);
  background: rgba(217, 119, 36, 0.04);
}

.provider-radio-card.selected {
  border-color: var(--color-accent, #d97724);
  background: var(--color-accent-subtle, rgba(217, 119, 36, 0.1));
  box-shadow: 0 0 0 1px var(--color-accent, #d97724);
}

.provider-card-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.provider-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.provider-card-header strong {
  font-size: 0.95rem;
  color: var(--color-text-primary, var(--ink));
}

.provider-card-content small {
  font-size: 0.77rem;
  color: var(--color-text-muted, var(--muted));
  line-height: 1.4;
}

.badge {
  font-size: 0.7rem;
  padding: 2px 7px;
  border-radius: 6px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.badge-ready {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.badge-warn {
  background: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

/* Readiness Cards Verticais no Step 0 */
.readiness-banner-vertical {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.readiness-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 10px;
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  transition: all 0.2s ease;
}

.readiness-card.ok {
  border-color: rgba(16, 185, 129, 0.3);
  background: rgba(16, 185, 129, 0.08);
}

.readiness-card-icon {
  margin-top: 1px;
  color: #f59e0b;
}

.readiness-card.ok .readiness-card-icon {
  color: #10b981;
}

.readiness-card-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.readiness-card-info strong {
  font-size: 0.85rem;
  color: var(--color-text-primary, var(--ink));
}

.readiness-card-info span {
  font-size: 0.77rem;
  color: var(--color-text-muted, var(--muted));
}

/* Chips Rápidos de Modelo */
.quick-chips-wrap {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chips-label {
  font-size: 0.78rem;
  color: var(--color-text-muted, var(--muted));
  font-weight: 500;
}

.quick-chips {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 9px;
}

.model-chip {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding: 9px 12px;
  border-radius: 9px;
  border: 1px solid var(--color-border-subtle, var(--line));
  background: var(--color-surface, var(--panel));
  color: var(--color-text-primary, var(--ink));
  cursor: pointer;
  text-align: left;
  transition: all 0.18s ease;
}

.model-chip:hover {
  border-color: var(--color-accent, #d97724);
  background: rgba(217, 119, 36, 0.05);
}

.model-chip.active {
  border-color: var(--color-accent, #d97724);
  background: var(--color-accent-subtle, rgba(217, 119, 36, 0.12));
}

.chip-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 6px;
}

.chip-title-row strong {
  font-size: 0.8rem;
  color: var(--color-text-primary, var(--ink));
}

.chip-badge {
  font-size: 0.65rem;
  padding: 1px 5px;
  border-radius: 4px;
  font-weight: 700;
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.model-chip small {
  font-size: 0.69rem;
  color: var(--color-text-muted, var(--muted));
  line-height: 1.3;
}

.credential-buttons-row {
  display: flex;
  gap: 10px;
  margin-top: 4px;
  flex-wrap: wrap;
}

.test-timestamp {
  font-size: 0.75rem;
  color: var(--color-text-muted, var(--muted));
  margin: 0;
}

.api-cost-note {
  font-size: 0.77rem;
  color: var(--color-text-muted, var(--muted));
  margin: 0;
}

.warning-text {
  color: var(--color-warning-text, #f59e0b);
  font-weight: 500;
}

.setting-save {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-top: 18px;
  border-top: 1px solid var(--color-border-subtle, var(--line));
  margin-top: 4px;
}

.setting-save .actions {
  display: flex;
  gap: 8px;
}

/* Responsividade fluida */
@media (max-width: 1100px) {
  .step-grid-2col,
  .provider-details-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 860px) {
  .settings-hub-layout {
    grid-template-columns: 1fr;
  }
  .settings-nav-sidebar {
    position: static;
  }
  .provider-switch-row,
  .quick-chips {
    grid-template-columns: 1fr;
  }
}
</style>
