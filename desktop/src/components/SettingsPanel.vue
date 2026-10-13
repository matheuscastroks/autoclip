<script setup lang="ts">
import AppButton from './AppButton.vue'
import AppSelect from './AppSelect.vue'
import {reactive,ref,watch,computed,onMounted,nextTick} from 'vue'
import {FolderOpen,KeyRound,Monitor,Save,Cpu,Sparkles,Scissors,CheckCircle2,AlertCircle,ChevronRight,ChevronLeft} from '@lucide/vue'
import {notify} from '../notifications'
import type {Config,GeminiConnection} from '../types'

const props=defineProps<{config:Config;saveConfig:(value:Config)=>Promise<unknown>;saveKey:(value:string)=>Promise<unknown>;pick:(kind:string)=>Promise<string|null>;getConnection?:()=>Promise<GeminiConnection>;testConnection?:()=>Promise<GeminiConnection>}>()
const values=reactive({clip_preferred_seconds:180,clip_max_seconds:300,pause_mode:'conservative' as const,show_thought_summaries:true,...props.config}),key=ref(''),busy=ref(false)
const settingsStep=ref(0)

const settingsCategories=[
  {num:'01',title:'Recursos locais',sub:'Whisper, FFmpeg e hardware local',icon:Cpu},
  {num:'02',title:'Gemini e modelo',sub:'Chave de API, conexão e catálogo',icon:Sparkles},
  {num:'03',title:'Preferências dos cortes',sub:'Duração, pausas e regras editoriais',icon:Scissors}
]
const settingsLabels=['Recursos locais','Gemini e modelo','Preferências dos cortes']

let invalidHandled=false
function invalidSetting(event:Event){event.preventDefault();if(invalidHandled)return;invalidHandled=true;const target=event.target as HTMLElement;const section=target.closest<HTMLElement>('[data-settings-step]');if(section)settingsStep.value=Number(section.dataset.settingsStep);for(let details=target.closest('details');details;details=details.parentElement?.closest('details')||null)details.open=true;notify.error('Confira os campos destacados desta etapa antes de salvar.');void nextTick(()=>{target.focus();invalidHandled=false})}
function settingsKey(e:KeyboardEvent){const k=e.key;let n=settingsStep.value;if(k==='ArrowRight'||k==='ArrowDown')n=(n+1)%3;else if(k==='ArrowLeft'||k==='ArrowUp')n=(n+2)%3;else if(k==='Home')n=0;else if(k==='End')n=2;else return;e.preventDefault();settingsStep.value=n;(e.currentTarget as HTMLElement).querySelectorAll<HTMLButtonElement>('button')[n]?.focus()}

const connection=ref<GeminiConnection|null>(null),validating=ref(false)
const statusLabel=computed(()=>validating.value?'Validando…':connection.value?.status==='valid'?'Conexão validada':connection.value?.status==='invalid'?'Chave sem acesso':connection.value?.status==='unavailable'?'Conexão indisponível':props.config.gemini_key_configured?'Chave salva · não testada':'Chave não configurada')
const models=computed(()=>connection.value?.models||[])
const modelOptions=computed(()=>[...(!models.value.some(m=>m.id===values.gemini_model)?[{value:values.gemini_model,label:values.gemini_model+' — '+(connection.value?.status==='valid'?'não aparece no catálogo':'modelo salvo'),disabled:true}]:[]),...models.value.map(m=>({value:m.id,label:m.display_name+' · '+m.id}))])
const listed=computed(()=>models.value.some(m=>m.id===values.gemini_model))
const missingModel=computed(()=>connection.value?.status==='valid'&&!listed.value)

watch(()=>props.config,(value,old)=>{for(const field of Object.keys(value) as (keyof Config)[]){if(value[field]!==old[field])Object.assign(values,{[field]:value[field]})}},{deep:true})
onMounted(async()=>{if(props.getConnection)try{connection.value=await props.getConnection()}catch(e){notify.error((e as Error).message)}})

async function execute(fn:()=>Promise<unknown>,success:string){busy.value=true;try{await fn();if(success)notify.success(success)}catch(e){notify.error((e as Error).message)}finally{busy.value=false}}
async function saveKey(){validating.value=true;await execute(async()=>{const result=await props.saveKey(key.value);if(result)connection.value=result as GeminiConnection;key.value='';if(!result||connection.value?.status==='valid')notify.success(result?'Conexão validada. Chave armazenada no Windows.':'Chave armazenada no Windows.');else notify.error(connection.value?.message||'Não foi possível validar a conexão.')},'');validating.value=false}
async function testConnection(){if(!props.testConnection)return;validating.value=true;await execute(async()=>{connection.value=await props.testConnection!();if(connection.value.status==='valid')notify.success('Conexão Gemini validada. Catálogo atualizado.');else notify.error(connection.value.message)},'');validating.value=false}
async function saveSettings(){if(values.clip_preferred_seconds>values.clip_max_seconds){notify.error('A duração preferida deve ser menor ou igual à máxima.');return}if(!missingModel.value)await execute(()=>props.saveConfig({...values}),'Configurações salvas.')}
async function pick(kind:string,field:'asr_model_path'|'ffmpeg'|'ffprobe'){await execute(async()=>{const result=await props.pick(kind);if(result)values[field]=result},'')}
</script>

<template>
  <div class="settings-workspace">
    <header class="page-heading">
      <div>
        <p class="breadcrumb">Preferências do aplicativo</p>
        <h1>Configurações</h1>
        <p>Ajuste os motores de IA, ferramentas de mídia e regras editoriais de cortes.</p>
      </div>
    </header>

    <div class="settings-hub-layout">
      <!-- Coluna esquerda: Menu Vertical de Categorias -->
      <aside class="settings-nav-sidebar">
        <nav class="settings-tiles" role="tablist" aria-label="Etapas de configuração" @keydown="settingsKey">
          <AppButton
            v-for="(cat,index) in settingsCategories"
            :key="cat.title"
            role="tab"
            :id="'settings-tab-'+index"
            :aria-selected="settingsStep===index"
            aria-controls="settings-content"
            :tabindex="settingsStep===index?0:-1"
            class="settings-category-btn"
            :class="{selected:settingsStep===index}"
            @click="settingsStep=index"
          >
            <span class="cat-num">{{cat.num}}</span>
            <div class="cat-content">
              <span class="cat-title">{{cat.title}}</span>
              <span class="cat-sub">{{cat.sub}}</span>
            </div>
            <div class="cat-indicator" :class="index===0?(config.asr_available&&config.tools_available?'ready':'warn'):index===1?(config.gemini_key_configured?'ready':'warn'):'ready'"></div>
          </AppButton>
        </nav>

        <div class="settings-sidebar-card">
          <div class="card-head">
            <Monitor :size="16"/>
            <strong>Ambiente Local-First</strong>
          </div>
          <p>Transcrição e renderização rodam 100% no seu computador usando CPU. Nenhum vídeo é enviado para a nuvem.</p>
        </div>
      </aside>

      <!-- Coluna direita: Painel Principal do Formulário -->
      <main class="settings-content-pane">
        <form id="settings-content" role="tabpanel" :aria-labelledby="'settings-tab-'+settingsStep" class="settings-main" :class="{'settings-gemini':settingsStep===1}" @submit.prevent="saveSettings" @invalid.capture="invalidSetting">
          
          <!-- Etapa 0: Recursos Locais -->
          <section v-show="settingsStep===0" data-settings-step="0" class="setting-section local-resources">
            <div class="section-title-wrap">
              <div class="section-icon"><Cpu :size="20"/></div>
              <div>
                <h2>Processamento local</h2>
                <p>Transcrição e renderização usam a CPU. Escolha os recursos já instalados.</p>
              </div>
            </div>

            <div class="readiness-banner">
              <div class="readiness-item" :class="{ok:config.asr_available}">
                <CheckCircle2 v-if="config.asr_available" :size="16"/>
                <AlertCircle v-else :size="16"/>
                <span>{{config.asr_available?'Modelo Whisper local pronto':'Modelo local não encontrado'}}</span>
              </div>
              <div class="readiness-item" :class="{ok:config.tools_available}">
                <CheckCircle2 v-if="config.tools_available" :size="16"/>
                <AlertCircle v-else :size="16"/>
                <span>{{config.tools_available?'FFmpeg e ffprobe prontos':'Ferramentas FFmpeg não encontradas'}}</span>
              </div>
            </div>

            <div class="local-resource-row">
              <label class="field">
                Pasta do modelo Whisper
                <span class="input-action">
                  <input v-model="values.asr_model_path" required placeholder="Caminho para o diretório do modelo Whisper..."/>
                  <AppButton type="button" class="icon-button" title="Escolher pasta do modelo" @click="pick('model','asr_model_path')"><FolderOpen :size="18"/></AppButton>
                </span>
                <small>Modelo multilíngue com suporte ao português; arquivos ficam locais.</small>
              </label>

              <div class="field-pair">
                <label class="field">
                  FFmpeg
                  <span class="input-action">
                    <input v-model="values.ffmpeg" required placeholder="Caminho para o executável ffmpeg..."/>
                    <AppButton type="button" class="icon-button" title="Localizar FFmpeg" @click="pick('ffmpeg','ffmpeg')"><FolderOpen :size="17"/></AppButton>
                  </span>
                </label>
                <label class="field">
                  ffprobe
                  <span class="input-action">
                    <input v-model="values.ffprobe" required placeholder="Caminho para o executável ffprobe..."/>
                    <AppButton type="button" class="icon-button" title="Localizar ffprobe" @click="pick('ffprobe','ffprobe')"><FolderOpen :size="17"/></AppButton>
                  </span>
                </label>
              </div>
            </div>
          </section>

          <!-- Etapa 1: Gemini & Seleção de Modelo -->
          <div v-show="settingsStep===1" data-settings-step="1" class="gemini-sections-wrap">
            <section class="credential-panel">
              <div class="section-title-wrap">
                <div class="section-icon"><KeyRound :size="20"/></div>
                <div class="title-with-pill">
                  <h2>Chave Gemini</h2>
                  <span class="status-pill" :data-status="validating?'running':connection?.status==='valid'?'completed':'pending'">
                    <i></i>{{statusLabel}}
                  </span>
                </div>
              </div>

              <p class="section-desc">Armazenada no Gerenciador de Credenciais do Windows. O aplicativo não exibe a chave salva.</p>

              <AppButton v-if="connection?.status==='invalid'||connection?.status==='unavailable'" type="button" class="text-button" @click="notify.error(connection!.message)">
                Ver motivo da falha
              </AppButton>

              <label class="field">
                {{config.gemini_key_configured?'Substituir chave':'Adicionar chave'}}
                <input type="password" @keydown.enter.prevent="!busy&&key.trim()&&saveKey()" v-model="key" autocomplete="new-password" placeholder="Cole sua chave de API do Google Gemini..."/>
              </label>

              <div class="credential-buttons-row">
                <AppButton type="button" class="button secondary" data-action="save-key" :disabled="busy||!key.trim()" @click="saveKey">
                  <KeyRound :size="16"/>{{validating?'Validando…':'Salvar e validar'}}
                </AppButton>
                <AppButton type="button" class="button secondary" data-action="test-gemini" :disabled="busy||!config.gemini_key_configured" @click="testConnection">
                  {{validating?'Validando…':'Testar conexão / Atualizar modelos'}}
                </AppButton>
              </div>

              <p v-if="connection?.checked_at" class="test-timestamp">Último teste: {{new Date(connection.checked_at).toLocaleString('pt-BR')}}</p>
              <p class="api-cost-note">O teste consulta apenas o catálogo. Não gera conteúdo nem consome cota de geração.</p>
            </section>

            <section class="setting-section">
              <div class="section-title-wrap">
                <div class="section-icon"><Sparkles :size="20"/></div>
                <div>
                  <h2>Seleção de trechos</h2>
                  <p>Projetos novos seguem da transcrição para a análise com Gemini automaticamente. O motor dimensiona as chamadas pelo conteúdo.</p>
                </div>
              </div>

              <label class="field">
                Modelo Gemini
                <AppSelect v-model="values.gemini_model" label="Modelo Gemini" data-field="gemini-model" :options="modelOptions" required :disabled="busy||!models.length"/>
                <small v-if="missingModel" class="warning-text">O modelo salvo não aparece no catálogo. Escolha outro modelo explicitamente.</small>
                <small v-else>{{models.length?models.length+' modelos disponíveis no catálogo.':'Teste a conexão para carregar os modelos disponíveis.'}}</small>
              </label>

              <details class="analysis-advanced">
                <summary>Ajustes avançados de análise</summary>
                <p>Você pode manter os padrões. A janela define quanto tempo da transcrição é analisado por vez; o limite de caracteres divide textos muito grandes. Esses valores não definem a duração dos cortes.</p>
                <div class="field-pair">
                  <label class="field">
                    Janela de análise (segundos)
                    <input type="number" v-model.number="values.window_seconds" min="60" max="1800" required/>
                  </label>
                  <label class="field">
                    Máximo de caracteres por janela
                    <input type="number" v-model.number="values.max_text_chars" min="1000" max="300000" required/>
                    <small>Limite aproximado do texto e identificadores por solicitação; não é um limite de tokens do modelo.</small>
                  </label>
                </div>
              </details>
            </section>
          </div>

          <!-- Etapa 2: Preferências dos Cortes -->
          <section v-show="settingsStep===2" data-settings-step="2" class="setting-section">
            <div class="section-title-wrap">
              <div class="section-icon"><Scissors :size="20"/></div>
              <div>
                <h2>Coerência, duração e pausas</h2>
                <p>Até 10 cortes por vídeo, com mínimo de 1 minuto e máximo de 5 minutos. Priorize concluir o argumento. Configurações valem para os próximos trabalhos.</p>
              </div>
            </div>

            <div class="field-pair">
              <label class="field">
                Duração preferida (segundos)
                <input type="number" data-field="clip-preferred" v-model.number="values.clip_preferred_seconds" min="60" max="300" required/>
                <small>Uma preferência recomendada; não força encerrar o raciocínio bruscamente.</small>
              </label>
              <label class="field">
                Duração máxima (segundos)
                <input type="number" data-field="clip-max" v-model.number="values.clip_max_seconds" min="60" max="300" required/>
                <small>De 60 a 300 segundos (1 a 5 minutos). Não recorta palavras para caber.</small>
              </label>
            </div>

            <label class="field">
              Pausas entre falas
              <AppSelect data-field="pause-mode" v-model="values.pause_mode" label="Pausas entre falas" :options="[{value:'preserve',label:'Preservar todas as pausas'},{value:'conservative',label:'Encurtar silêncios longos com verificação no áudio'}]"/>
              <small>Detecção de voz e volume, com margens de proteção. Respirações curtas permanecem. Confira as junções na revisão.</small>
            </label>

            <label class="check-row">
              <input type="checkbox" data-field="thought-summaries" v-model="values.show_thought_summaries"/>
              <span>Mostrar resumos de análise enviados pelo Gemini</span>
            </label>

            <details class="thought-help">
              <summary>Sobre os resumos do Gemini</summary>
              <p class="subtle">Disponibilidade depende do modelo e da API. Resumos não mostram o pensamento interno completo. Modelos com pensamento habilitado podem consumir mais tokens.</p>
            </details>
          </section>

          <!-- Barra Persistente de Ações -->
          <div class="setting-save">
            <AppButton class="button primary" data-action="save-config" :disabled="busy||missingModel">
              <Save :size="16"/>Salvar configurações
            </AppButton>
            <div class="actions">
              <AppButton v-if="settingsStep>0" type="button" class="button secondary" @click="settingsStep--">
                <ChevronLeft :size="15"/>Anterior
              </AppButton>
              <AppButton v-if="settingsStep<2" type="button" class="button secondary" @click="settingsStep++">
                Próximo passo<ChevronRight :size="15"/>
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
}

.settings-hub-layout {
  display: grid;
  grid-template-columns: 290px minmax(0, 1fr);
  gap: 22px;
  align-items: start;
}

.settings-nav-sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
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
  border-color: var(--color-accent, #6366f1);
  color: var(--color-accent-text, var(--accent));
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

.settings-sidebar-card {
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: var(--radius-panel, 14px);
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.settings-sidebar-card .card-head {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-primary, var(--ink));
  font-size: 0.82rem;
}

.settings-sidebar-card p {
  font-size: 0.77rem;
  line-height: 1.5;
  color: var(--color-text-muted, var(--muted));
  margin: 0;
}

.settings-content-pane {
  min-width: 0;
}

.settings-main {
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: var(--radius-panel, 14px);
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-title-wrap {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  margin-bottom: 16px;
}

.section-icon {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  background: var(--color-surface-hover, var(--soft));
  color: var(--color-accent, #6366f1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.title-with-pill {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.section-title-wrap h2 {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 4px;
  color: var(--color-text-primary, var(--ink));
}

.section-title-wrap p {
  margin: 0;
  font-size: 0.83rem;
  color: var(--color-text-muted, var(--muted));
}

.readiness-banner {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.readiness-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  background: var(--color-surface-hover, var(--soft));
  border: 1px solid var(--color-border-subtle, var(--line));
  font-size: 0.8rem;
  color: var(--color-text-muted, var(--muted));
}

.readiness-item.ok {
  color: #10b981;
  border-color: rgba(16, 185, 129, 0.25);
  background: rgba(16, 185, 129, 0.08);
}

.credential-buttons-row {
  display: flex;
  gap: 10px;
  margin-top: 14px;
  flex-wrap: wrap;
}

.test-timestamp {
  font-size: 0.75rem;
  color: var(--color-text-muted, var(--muted));
  margin-top: 10px;
}

.api-cost-note {
  font-size: 0.77rem;
  color: var(--color-text-muted, var(--muted));
  margin-top: 6px;
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
  margin-top: 8px;
}

.setting-save .actions {
  display: flex;
  gap: 8px;
}

@media (max-width: 900px) {
  .settings-hub-layout {
    grid-template-columns: 1fr;
  }
}
</style>
