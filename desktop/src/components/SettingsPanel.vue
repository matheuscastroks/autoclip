<script setup lang="ts">
import AppIcon from './ui/AppIcon.vue';
import AppButton from './AppButton.vue';
import AppSelect from './AppSelect.vue';
import { reactive, ref, watch, computed, onMounted, nextTick } from 'vue';
import { notify } from '../notifications';
import type { Config, GeminiConnection } from '../types';

const props = defineProps<{
  config: Config;
  saveConfig: (value: Config) => Promise<unknown>;
  saveKey: (value: string) => Promise<unknown>;
  saveOpenRouterKey?: (value: string) => Promise<unknown>;
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
  video_preset: (props.config.video_preset || 'karaoke_yellow') as 'karaoke_yellow' | 'editorial_sober' | 'documentary' | 'impact',
  playback_speed: (props.config.playback_speed || '1x') as '1x' | '1.25x' | '1.5x',
  ...props.config,
});

const key = ref(''),
  openrouterKey = ref(''),
  busy = ref(false);
const settingsStep = ref(0);

const settingsCategories = [
  { title: 'Recursos locais', sub: 'Whisper, FFmpeg e aceleração' },
  { title: 'IA e modelos', sub: 'Gemini, OpenRouter e chaves' },
  { title: 'Duração dos cortes', sub: 'Tempo alvo e limite máximo' },
  { title: 'Aparência dos vídeos', sub: 'Estilo visual e velocidade' },
];

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
  notify.error('Confira os campos destacados antes de salvar.');
  void nextTick(() => {
    target.focus();
    invalidHandled = false;
  });
}

function settingsKey(e: KeyboardEvent) {
  const k = e.key;
  const count = settingsCategories.length;
  let n = settingsStep.value;
  if (k === 'ArrowRight' || k === 'ArrowDown') n = (n + 1) % count;
  else if (k === 'ArrowLeft' || k === 'ArrowUp') n = (n + count - 1) % count;
  else if (k === 'Home') n = 0;
  else if (k === 'End') n = count - 1;
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

async function handleSaveKey() {
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

async function handleSaveOpenRouterKey() {
  const saveFn = props.saveOpenRouterKey;
  if (!saveFn) {
    notify.error('Função para salvar chave OpenRouter não está disponível.');
    return;
  }
  validating.value = true;
  await execute(async () => {
    await saveFn(openrouterKey.value.trim());
    openrouterKey.value = '';
    values.openrouter_key_configured = true;
    notify.success('Chave OpenRouter armazenada no Windows com segurança.');
  }, '');
  validating.value = false;
}

async function handleTestConnection() {
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

async function handlePick(kind: string, field: 'asr_model_path' | 'ffmpeg' | 'ffprobe') {
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
        <h1>Configurações</h1>
        <p>Preferências de processamento, inteligência artificial e cortes.</p>
      </div>
    </header>

    <div class="settings-hub-layout">
      <!-- Coluna esquerda: Menu Vertical de Categorias -->
      <aside class="settings-nav-sidebar">
        <nav
          class="settings-tiles"
          role="tablist"
          aria-label="Categorias de configuração"
          aria-orientation="vertical"
          @keydown="settingsKey"
        >
          <button
            v-for="(cat, index) in settingsCategories"
            :id="'settings-tab-' + index"
            :key="cat.title"
            role="tab"
            :aria-selected="settingsStep === index"
            aria-controls="settings-content"
            :tabindex="settingsStep === index ? 0 : -1"
            type="button"
            class="settings-category-btn"
            :class="{ selected: settingsStep === index }"
            @click="settingsStep = index"
          >
            <div class="cat-content">
              <span class="cat-title">{{ cat.title }}</span>
              <span class="cat-sub">{{ cat.sub }}</span>
            </div>
            <div
              aria-hidden="true"
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
          </button>
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
          <!-- Recursos locais -->
          <div
            v-show="settingsStep === 0"
            data-settings-step="0"
            class="step-grid-2col local-resources"
          >
            <!-- Coluna 1: Diagnóstico e Ambiente Local -->
            <section class="setting-section">
              <div class="section-title-wrap">
                <div>
                  <h2>Ambiente local</h2>
                </div>
              </div>

              <div class="readiness-banner-vertical">
                <div class="readiness-card" :class="{ ok: config.asr_available }">
                  <div class="readiness-card-icon">
                    <AppIcon v-if="config.asr_available" name="check-circle" size="md" />
                    <AppIcon v-else name="warning" size="md" />
                  </div>
                  <div class="readiness-card-info">
                    <strong>Transcrição · Whisper</strong>
                    <span>{{
                      config.asr_available
                        ? 'Modelo local encontrado e pronto para uso'
                        : 'Modelo local não encontrado no diretório'
                    }}</span>
                  </div>
                </div>

                <div class="readiness-card" :class="{ ok: config.tools_available }">
                  <div class="readiness-card-icon">
                    <AppIcon v-if="config.tools_available" name="check-circle" size="md" />
                    <AppIcon v-else name="warning" size="md" />
                  </div>
                  <div class="readiness-card-info">
                    <strong>Vídeo · FFmpeg e ffprobe</strong>
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
            <details class="setting-section settings-paths">
              <summary>Caminhos técnicos</summary>
              <div class="section-title-wrap">
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
                        @click="handlePick('model', 'asr_model_path')"
                        ><AppIcon name="folder-open" size="md"
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
                        @click="handlePick('ffmpeg', 'ffmpeg')"
                        ><AppIcon name="folder-open" size="md"
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
                        @click="handlePick('ffprobe', 'ffprobe')"
                        ><AppIcon name="folder-open" size="md"
                      /></AppButton>
                    </el-tooltip>
                  </span>
                  <small>Usado para inspeção técnica e validação dos streams de vídeo.</small>
                </label>
              </div>
            </details>
          </div>

          <!-- Etapa 1: IA & Provedor -->
          <div v-show="settingsStep === 1" data-settings-step="1" class="step-ia-wrap">
            <!-- Provedor de IA -->
            <section class="setting-section provider-selector-section">
              <div class="section-title-wrap">
                <div>
                  <h2 id="settings-provider-heading">Serviço de análise</h2>
                  <p>
                    Selecione o serviço de IA utilizado após a transcrição para analisar argumentos
                    e sugerir cortes.
                  </p>
                </div>
              </div>

              <fieldset class="provider-choice-group" aria-labelledby="settings-provider-heading">
                <div class="provider-switch-row">
                  <label
                    class="provider-radio-card"
                    :class="{ selected: values.ai_provider === 'gemini' }"
                    @click="values.ai_provider = 'gemini'"
                  >
                    <input
                      v-model="values.ai_provider"
                      type="radio"
                      name="ai-provider"
                      value="gemini"
                      data-field="provider-gemini"
                      @change="values.ai_provider = 'gemini'"
                    />
                    <div class="provider-card-content">
                      <div class="provider-card-header">
                        <strong>Google Gemini</strong>
                      </div>
                      <small
                        >Modelos Google, com catálogo e conexão validados pelo aplicativo.</small
                      >
                    </div>
                  </label>

                  <label
                    class="provider-radio-card"
                    :class="{ selected: values.ai_provider === 'openrouter' }"
                    @click="values.ai_provider = 'openrouter'"
                  >
                    <input
                      v-model="values.ai_provider"
                      type="radio"
                      name="ai-provider"
                      value="openrouter"
                      data-field="provider-openrouter"
                      @change="values.ai_provider = 'openrouter'"
                    />
                    <div class="provider-card-content">
                      <div class="provider-card-header">
                        <strong>OpenRouter</strong>
                      </div>
                      <small
                        >Acesso a diferentes modelos. Preço e disponibilidade dependem do
                        modelo.</small
                      >
                    </div>
                  </label>
                </div>
              </fieldset>
            </section>

            <!-- Credenciais e modelo do provedor selecionado -->
            <div class="provider-details-grid">
              <!-- PROVEDOR: GEMINI -->
              <template v-if="values.ai_provider === 'gemini'">
                <!-- Coluna 1: Credencial Gemini -->
                <section class="credential-panel">
                  <div class="section-title-wrap">
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
                      v-model="key"
                      type="password"
                      autocomplete="new-password"
                      placeholder="Cole sua chave de API do Google Gemini..."
                      @keydown.enter.prevent="!busy && key.trim() && handleSaveKey()"
                    />
                  </label>

                  <div class="credential-buttons-row">
                    <AppButton
                      type="button"
                      class="button secondary"
                      data-action="save-key"
                      :disabled="busy || !key.trim()"
                      @click="handleSaveKey"
                    >
                      <AppIcon name="key" size="sm" />{{
                        validating ? 'Validando…' : 'Salvar e validar'
                      }}
                    </AppButton>
                    <AppButton
                      type="button"
                      class="button secondary"
                      data-action="test-gemini"
                      :disabled="busy || !config.gemini_key_configured"
                      @click="handleTestConnection"
                    >
                      {{ validating ? 'Validando…' : 'Testar conexão' }}
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
                    <div>
                      <h2>Seleção de trechos</h2>
                      <p>Defina o modelo que analisa a transcrição e sugere os cortes.</p>
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
                      v-model="openrouterKey"
                      type="password"
                      autocomplete="new-password"
                      placeholder="Cole sua chave sk-or-v1-..."
                      @keydown.enter.prevent="
                        !busy && openrouterKey.trim() && handleSaveOpenRouterKey()
                      "
                    />
                  </label>

                  <div class="credential-buttons-row">
                    <AppButton
                      type="button"
                      class="button secondary"
                      data-action="save-openrouter-key"
                      :disabled="busy || !openrouterKey.trim()"
                      @click="handleSaveOpenRouterKey"
                    >
                      <AppIcon name="key" size="sm" />{{
                        validating ? 'Salvando…' : 'Salvar chave OpenRouter'
                      }}
                    </AppButton>
                  </div>
                </section>

                <!-- Coluna 2: Modelo OpenRouter & Chips Rápidos -->
                <section class="setting-section">
                  <div class="section-title-wrap">
                    <div>
                      <h2>Modelo OpenRouter</h2>
                      <p>Escolha um atalho ou informe o identificador de um modelo do catálogo.</p>
                    </div>
                  </div>

                  <div class="quick-chips-wrap">
                    <span class="chips-label">Modelos sugeridos:</span>
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
                <div>
                  <h2>Duração dos cortes</h2>
                  <p>
                    Objetivos editoriais para a inteligência artificial. Prioriza argumentos completos e coesão narrativa.
                  </p>
                </div>
              </div>

              <div class="field-pair">
                <label class="field">
                  Duração preferida (segundos)
                  <input
                    v-model.number="values.clip_preferred_seconds"
                    type="number"
                    data-field="clip-preferred"
                    min="60"
                    max="300"
                    required
                  />
                  <small>Duração alvo recomendada (60 a 300 segundos).</small>
                </label>
                <label class="field">
                  Duração máxima sugerida (segundos)
                  <input
                    v-model.number="values.clip_max_seconds"
                    type="number"
                    data-field="clip-max"
                    min="60"
                    max="300"
                    required
                  />
                  <small>Teto editorial sugerido para a IA fechar o raciocínio.</small>
                </label>
              </div>

              <div class="editorial-options">
                <label class="check-row">
                  <input
                    v-model="values.show_thought_summaries"
                    type="checkbox"
                    data-field="thought-summaries"
                  />
                  <span>Mostrar resumos de análise enviados pela IA</span>
                </label>
              </div>
            </section>
          </div>

          <!-- Etapa 3: Aparência dos vídeos -->
          <div v-show="settingsStep === 3" data-settings-step="3" class="step-appearance-wrap">
            <section class="setting-section">
              <div class="section-title-wrap">
                <div>
                  <h2 id="settings-preset-heading">Estilo visual dos cortes</h2>
                  <p>
                    Escolha um dos quatro estilos predefinidos para títulos de abertura e legendas.
                    As cores e tipografia são cuidadosamente calibradas para máxima legibilidade.
                  </p>
                </div>
              </div>

              <fieldset class="preset-choice-group" aria-labelledby="settings-preset-heading">
                <div class="preset-cards-grid">
                  <!-- Karaokê Amarelo -->
                  <label
                    class="preset-card"
                    :class="{ selected: values.video_preset === 'karaoke_yellow' }"
                    @click="values.video_preset = 'karaoke_yellow'"
                  >
                    <input
                      v-model="values.video_preset"
                      type="radio"
                      name="video-preset"
                      value="karaoke_yellow"
                      data-field="preset-karaoke_yellow"
                      @change="values.video_preset = 'karaoke_yellow'"
                    />
                    <div class="preset-card-content">
                      <div class="preset-card-header">
                        <div class="preset-title-wrap">
                          <strong>Karaokê Amarelo</strong>
                          <span class="preset-default-badge">Padrão</span>
                        </div>
                        <div class="preset-sample sample-karaoke" aria-hidden="true">
                          <span class="sample-title-card sample-yellow">TÍTULO INICIAL</span>
                          <span class="sample-caption">palavra <b class="highlight-yellow">ativa</b> em vídeo</span>
                        </div>
                      </div>
                      <small>Palavras ativas amarelas com destaque dinâmico e título de abertura em faixa amarela com texto preto.</small>
                    </div>
                  </label>

                  <!-- Editorial Sóbrio -->
                  <label
                    class="preset-card"
                    :class="{ selected: values.video_preset === 'editorial_sober' }"
                    @click="values.video_preset = 'editorial_sober'"
                  >
                    <input
                      v-model="values.video_preset"
                      type="radio"
                      name="video-preset"
                      value="editorial_sober"
                      data-field="preset-editorial_sober"
                      @change="values.video_preset = 'editorial_sober'"
                    />
                    <div class="preset-card-content">
                      <div class="preset-card-header">
                        <div class="preset-title-wrap">
                          <strong>Editorial Sóbrio</strong>
                        </div>
                        <div class="preset-sample sample-editorial" aria-hidden="true">
                          <span class="sample-title-card sample-sober">TÍTULO INICIAL</span>
                          <span class="sample-caption">legendas estáticas e discretas</span>
                        </div>
                      </div>
                      <small>Legendas estáticas e discretas com tipografia limpa, tons neutros e composição formal minimalista.</small>
                    </div>
                  </label>

                  <!-- Documental -->
                  <label
                    class="preset-card"
                    :class="{ selected: values.video_preset === 'documentary' }"
                    @click="values.video_preset = 'documentary'"
                  >
                    <input
                      v-model="values.video_preset"
                      type="radio"
                      name="video-preset"
                      value="documentary"
                      data-field="preset-documentary"
                      @change="values.video_preset = 'documentary'"
                    />
                    <div class="preset-card-content">
                      <div class="preset-card-header">
                        <div class="preset-title-wrap">
                          <strong>Documental</strong>
                        </div>
                        <div class="preset-sample sample-documentary" aria-hidden="true">
                          <span class="sample-title-card sample-blue">TÍTULO INICIAL</span>
                          <span class="sample-caption sample-bar">faixa inferior escura · azul-aço</span>
                        </div>
                      </div>
                      <small>Legendas em faixa inferior sombreada com paleta escura cinematográfica e detalhes em azul-aço.</small>
                    </div>
                  </label>

                  <!-- Impacto -->
                  <label
                    class="preset-card"
                    :class="{ selected: values.video_preset === 'impact' }"
                    @click="values.video_preset = 'impact'"
                  >
                    <input
                      v-model="values.video_preset"
                      type="radio"
                      name="video-preset"
                      value="impact"
                      data-field="preset-impact"
                      @change="values.video_preset = 'impact'"
                    />
                    <div class="preset-card-content">
                      <div class="preset-card-header">
                        <div class="preset-title-wrap">
                          <strong>Impacto</strong>
                        </div>
                        <div class="preset-sample sample-impact" aria-hidden="true">
                          <span class="sample-title-card sample-coral">TÍTULO INICIAL</span>
                          <span class="sample-caption"><b class="highlight-coral">impacto cinético</b></span>
                        </div>
                      </div>
                      <small>Destaque cinético em tom coral vibrante com animações sutis de entrada e visual de alto contraste.</small>
                    </div>
                  </label>
                </div>
              </fieldset>
            </section>

            <section class="setting-section speed-section">
              <div class="section-title-wrap">
                <div>
                  <h2 id="settings-speed-heading">Velocidade do vídeo exportado</h2>
                  <p>
                    Acelera o vídeo gerado preservando rigorosamente o tom natural da voz, com legendas sincronizadas à duração final.
                  </p>
                </div>
              </div>

              <fieldset class="speed-choice-group" aria-labelledby="settings-speed-heading">
                <div class="speed-selector-row">
                  <label
                    class="speed-radio-card"
                    :class="{ selected: values.playback_speed === '1x' }"
                    @click="values.playback_speed = '1x'"
                  >
                    <input
                      v-model="values.playback_speed"
                      type="radio"
                      name="playback-speed"
                      value="1x"
                      data-field="speed-1x"
                      @change="values.playback_speed = '1x'"
                    />
                    <div class="speed-card-content">
                      <span class="speed-badge">1×</span>
                      <strong>Normal</strong>
                      <small>Velocidade original (100%)</small>
                    </div>
                  </label>

                  <label
                    class="speed-radio-card"
                    :class="{ selected: values.playback_speed === '1.25x' }"
                    @click="values.playback_speed = '1.25x'"
                  >
                    <input
                      v-model="values.playback_speed"
                      type="radio"
                      name="playback-speed"
                      value="1.25x"
                      data-field="speed-1.25x"
                      @change="values.playback_speed = '1.25x'"
                    />
                    <div class="speed-card-content">
                      <span class="speed-badge">1,25×</span>
                      <strong>Ágil</strong>
                      <small>25% mais rápido · ritmo dinâmico</small>
                    </div>
                  </label>

                  <label
                    class="speed-radio-card"
                    :class="{ selected: values.playback_speed === '1.5x' }"
                    @click="values.playback_speed = '1.5x'"
                  >
                    <input
                      v-model="values.playback_speed"
                      type="radio"
                      name="playback-speed"
                      value="1.5x"
                      data-field="speed-1.5x"
                      @change="values.playback_speed = '1.5x'"
                    />
                    <div class="speed-card-content">
                      <span class="speed-badge">1,5×</span>
                      <strong>Rápido</strong>
                      <small>50% mais rápido · síntese direta</small>
                    </div>
                  </label>
                </div>
              </fieldset>
            </section>
          </div>

          <!-- Barra Persistente de Ações -->
          <div class="setting-save">
            <AppButton
              type="submit"
              class="button primary"
              data-action="save-config"
              :disabled="busy || missingModel"
            >
              <AppIcon name="save" size="sm" />{{ busy ? 'Salvando…' : 'Salvar configurações' }}
            </AppButton>
            <p class="save-hint">
              As preferências são aplicadas ao salvar. Chaves são salvas separadamente.
            </p>
          </div>
        </form>
      </main>
    </div>
  </div>
</template>

<style scoped>
.settings-workspace {
  width: 100%;
  max-width: 1200px;
  margin-inline: auto;
  padding-bottom: 16px;
}
.settings-workspace .page-heading {
  margin-bottom: 28px;
}
.settings-hub-layout {
  display: grid;
  grid-template-columns: 210px minmax(0, 1fr);
  gap: 40px;
  align-items: start;
}
.settings-nav-sidebar {
  position: sticky;
  top: 20px;
}
.settings-workspace .settings-tiles {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 0;
  margin: 0;
}
.settings-workspace .settings-tiles .settings-category-btn {
  width: 100%;
  height: auto;
  min-height: 56px;
  margin: 0;
  padding: 12px;
  border: 1px solid transparent;
  border-radius: var(--radius-control);
  background: transparent;
  color: var(--color-text-secondary);
  text-align: left;
  justify-content: flex-start;
  white-space: normal;
}
.settings-workspace .settings-category-btn :deep(> span) {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 12px;
}
.settings-workspace .settings-tiles .settings-category-btn:hover {
  background: var(--color-surface);
  color: var(--ink);
}
.settings-workspace .settings-tiles .settings-category-btn.selected {
  background: var(--color-surface-selected);
  color: var(--ink);
}
.cat-content {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 5px;
  min-width: 0;
}
.cat-title {
  font-size: 13px;
  font-weight: 600;
  line-height: 1.4;
}
.cat-sub {
  font-size: var(--font-size-meta);
  color: var(--color-text-muted);
  line-height: 1.5;
}
.cat-indicator {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--color-text-muted);
}
.cat-indicator.warn {
  background: var(--color-warning-text);
}
.settings-content-pane {
  min-width: 0;
}
.settings-workspace .settings-main {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  min-width: 0;
}
.step-grid-2col,
.step-ia-wrap,
.step-cuts-wrap,
.provider-details-grid {
  display: flex;
  flex-direction: column;
  gap: 0;
  min-width: 0;
}
.settings-workspace .setting-section,
.settings-workspace .credential-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px 0;
  margin: 0;
  min-width: 0;
  background: transparent;
  border: 0;
  border-bottom: 1px solid var(--line);
  border-radius: 0;
}
.settings-workspace [data-settings-step] > .setting-section:first-child {
  padding-top: 0;
}
.section-title-wrap {
  display: flex;
  align-items: start;
  gap: 12px;
}
.section-title-wrap h2 {
  margin: 0;
  color: var(--ink);
  font-size: 15px;
  font-weight: 600;
  line-height: 1.5;
}
.section-title-wrap p,
.settings-workspace .credential-panel p,
.section-desc {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-control);
  line-height: 1.6;
}
.title-with-pill {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}
.fields-stack {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.settings-workspace .settings-main .field {
  margin: 0;
  gap: 8px;
  min-width: 0;
  font-size: var(--font-size-control);
}
.settings-workspace .field small {
  font-size: var(--font-size-meta);
  line-height: 1.6;
  color: var(--color-text-muted);
}
.settings-workspace .input-action {
  min-width: 0;
}
.settings-workspace .input-action input {
  min-width: 0;
  width: 100%;
  font-size: var(--font-size-control);
}
.readiness-banner-vertical {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
.readiness-card {
  display: flex;
  gap: 10px;
  align-items: start;
}
.readiness-card-icon {
  color: var(--color-warning-text);
  padding-top: 1px;
}
.readiness-card.ok .readiness-card-icon {
  color: var(--color-text-secondary);
}
.readiness-card-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.readiness-card-info strong {
  font-size: var(--font-size-control);
  font-weight: 500;
}
.readiness-card-info span {
  font-size: var(--font-size-meta);
  line-height: 1.6;
  color: var(--color-text-muted);
}
.provider-switch-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.provider-choice-group {
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
}
.provider-radio-card {
  display: flex;
  align-items: start;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--line-strong);
  border-radius: var(--radius-control);
  cursor: pointer;
}
.provider-radio-card.selected {
  background: var(--color-surface);
  border-color: var(--color-text-muted);
}
.provider-radio-card:focus-within {
  outline: 2px solid var(--focus-ring);
  outline-offset: 3px;
}
.provider-radio-card input {
  margin-top: 3px;
  accent-color: var(--color-action-primary);
}
.provider-card-content {
  display: flex;
  flex: 1;
  min-width: 0;
  flex-direction: column;
  gap: 8px;
}
.provider-card-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.provider-card-header strong {
  font-size: 13px;
  font-weight: 600;
}
.provider-card-header .badge {
  display: none;
}
.provider-card-content small {
  font-size: var(--font-size-meta);
  line-height: 1.6;
  color: var(--color-text-muted);
}
.credential-buttons-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.settings-workspace .status-pill {
  background: transparent;
  border-color: var(--line-strong);
  color: var(--color-text-secondary);
}
.settings-workspace .status-pill[data-status='running'] {
  color: var(--color-warning-text);
}
.settings-workspace .test-timestamp,
.settings-workspace .api-cost-note {
  margin: 0;
  font-size: var(--font-size-meta);
  color: var(--color-text-muted);
}
.quick-chips-wrap {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.chips-label {
  font-size: var(--font-size-meta);
  color: var(--color-text-muted);
}
.quick-chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.model-chip {
  padding: 7px 10px;
  background: transparent;
  color: var(--color-text-secondary);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius-control);
  cursor: pointer;
}
.model-chip:hover,
.model-chip.active {
  background: var(--color-surface-selected);
  color: var(--ink);
}
.chip-title-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.chip-title-row strong {
  font-size: var(--font-size-meta);
  font-weight: 500;
}
.model-chip small,
.chip-badge {
  display: none;
}
.settings-workspace .field .warning-text {
  color: var(--color-warning-text);
}
.field-pair {
  max-width: 560px;
  gap: 24px;
}
.editorial-options {
  padding-top: 8px;
}
.check-row {
  font-size: var(--font-size-control);
}
.provider-details-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 28px;
}
.provider-details-grid > section {
  border-bottom: 0;
}
.settings-workspace .settings-main .setting-save {
  position: sticky;
  bottom: 0;
  z-index: 2;
  display: flex;
  flex-direction: row-reverse;
  align-items: center;
  gap: 24px;
  padding: 16px 0;
  border-top: 1px solid var(--line);
  background: var(--canvas);
}
.save-hint {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-meta);
  line-height: 1.6;
  flex: 1;
  max-width: 42ch;
}
.settings-workspace .setting-save :deep(.el-button) {
  background-color: var(--color-action-primary) !important;
  border-color: var(--color-action-primary) !important;
  color: var(--color-action-primary-text) !important;
}
.settings-workspace .setting-save :deep(.el-button:hover:not(:disabled)) {
  background-color: var(--color-action-primary-hover) !important;
  border-color: var(--color-action-primary-hover) !important;
}
@media (max-width: 1100px) {
  .settings-hub-layout {
    grid-template-columns: 180px minmax(0, 1fr);
    gap: 28px;
  }
  .provider-switch-row,
  .provider-details-grid,
  .readiness-banner-vertical {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}
@media (max-width: 760px) {
  .settings-workspace .page-heading {
    margin-bottom: 20px;
  }
  .settings-hub-layout {
    grid-template-columns: 1fr;
    gap: 24px;
  }
  .settings-nav-sidebar {
    position: static;
  }
  .settings-workspace .settings-tiles {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 4px;
  }
  .settings-workspace .settings-tiles .settings-category-btn {
    width: auto;
    min-height: 40px;
    padding: 8px 12px;
  }
  .cat-sub,
  .cat-indicator {
    display: none;
  }
  .field-pair {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  .settings-workspace .settings-main .setting-save {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
}

/* Aparência dos vídeos: Estilos Visuais e Velocidade */
.step-appearance-wrap {
  display: flex;
  flex-direction: column;
  gap: 32px;
}
.preset-choice-group,
.speed-choice-group {
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
}
.preset-cards-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.preset-card {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--color-border-subtle, rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-card, 8px);
  background: var(--color-surface, #1e2227);
  cursor: pointer;
  transition: border-color 0.18s ease, background-color 0.18s ease, box-shadow 0.18s ease;
}
.preset-card:hover {
  border-color: var(--color-border-hover, rgba(255, 255, 255, 0.25));
  background: var(--color-surface-hover, #242930);
}
.preset-card.selected {
  border-color: var(--color-primary, #ffd700);
  background: var(--color-surface-selected, rgba(255, 215, 0, 0.05));
  box-shadow: 0 0 0 1px var(--color-primary, #ffd700);
}
.preset-card input[type="radio"] {
  margin-top: 3px;
  accent-color: var(--color-primary, #ffd700);
}
.preset-card-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
  min-width: 0;
}
.preset-card-header {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.preset-title-wrap {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.preset-title-wrap strong {
  font-size: var(--font-size-body, 14px);
  font-weight: 600;
  color: var(--ink, #fff);
}
.preset-default-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--color-primary, #ffd700);
  color: #000;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.preset-sample {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 12px 10px;
  border-radius: 6px;
  background: #101316;
  border: 1px solid rgba(255, 255, 255, 0.06);
  min-height: 64px;
}
.sample-title-card {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 1px;
  padding: 2px 8px;
  border-radius: 3px;
}
.sample-yellow {
  background: #ffd700;
  color: #000;
}
.sample-sober {
  background: #2a2e35;
  color: #f0f0f0;
  border: 1px solid rgba(255, 255, 255, 0.15);
}
.sample-blue {
  background: #1e3a5f;
  color: #b0c4de;
  border-left: 3px solid #4682b4;
}
.sample-coral {
  background: #ff6b6b;
  color: #fff;
  font-style: italic;
}
.sample-caption {
  font-size: 11px;
  color: #d1d5db;
}
.highlight-yellow {
  color: #ffd700;
  font-weight: 700;
}
.highlight-coral {
  color: #ff6b6b;
  font-weight: 700;
}
.sample-bar {
  background: rgba(0, 0, 0, 0.6);
  padding: 1px 6px;
  border-radius: 2px;
  border-bottom: 2px solid #4682b4;
}
.preset-card small {
  font-size: 12px;
  color: var(--color-text-secondary, #9ca3af);
  line-height: 1.4;
}

/* Seletor de Velocidade */
.speed-section {
  margin-top: 16px;
}
.speed-selector-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.speed-radio-card {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 14px 16px;
  border: 1px solid var(--color-border-subtle, rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-card, 8px);
  background: var(--color-surface, #1e2227);
  cursor: pointer;
  transition: border-color 0.18s ease, background-color 0.18s ease;
}
.speed-radio-card:hover {
  border-color: var(--color-border-hover, rgba(255, 255, 255, 0.25));
  background: var(--color-surface-hover, #242930);
}
.speed-radio-card.selected {
  border-color: var(--color-primary, #ffd700);
  background: var(--color-surface-selected, rgba(255, 215, 0, 0.05));
  box-shadow: 0 0 0 1px var(--color-primary, #ffd700);
}
.speed-radio-card input[type="radio"] {
  margin-top: 2px;
  accent-color: var(--color-primary, #ffd700);
}
.speed-card-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.speed-badge {
  display: inline-block;
  align-self: flex-start;
  font-size: 11px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 3px;
  background: rgba(255, 255, 255, 0.08);
  color: var(--ink, #fff);
}
.speed-card-content strong {
  font-size: 14px;
  color: var(--ink, #fff);
}
.speed-card-content small {
  font-size: 12px;
  color: var(--color-text-secondary, #9ca3af);
  line-height: 1.3;
}
@media (max-width: 800px) {
  .preset-cards-grid,
  .speed-selector-row {
    grid-template-columns: 1fr;
  }
}
</style>
