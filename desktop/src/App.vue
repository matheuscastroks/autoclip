<script setup lang="ts">
import AppButton from './components/AppButton.vue'
import {computed,onMounted,onUnmounted,ref} from 'vue'
import {Scissors,Layers,Settings2,HardDrive,Plus,FileVideo,Link,FolderOpen,X,RefreshCw,LoaderCircle,ListOrdered,Sparkles,Check,AlertTriangle} from '@lucide/vue'
import {api} from './api'
import type {Project,Config,Job,Transcript,Revision,Decision,AnalysisView,AnalysisSelection,HardwareProfile} from './types'
import {active} from './format'
import ProjectLibrary from './components/ProjectLibrary.vue'
import ProjectWorkspace from './components/ProjectWorkspace.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import GlobalQueueModal from './components/GlobalQueueModal.vue'
import OnboardingModal from './components/OnboardingModal.vue'
import {ElConfigProvider} from 'element-plus'
import ptBr from 'element-plus/es/locale/lang/pt-br'
import {notify,createJobNotifier} from './notifications'
const projects=ref<Project[]>([]),config=ref<Config|null>(null),jobs=ref<Job[]>([]),project=ref<Project|null>(null),transcript=ref<Transcript|null>(null),revisions=ref<Revision[]>([])
const showGlobalQueue=ref(false),hardwareProfile=ref<HardwareProfile|null>(null),onboardingDismissed=ref(false)
const showOnboarding=computed(()=>{
  if(onboardingDismissed.value||!config.value)return false
  return !config.value.tools_available||!config.value.asr_available
})
async function onDependenciesConfigured(){config.value=await api.config()}
const activeJobsCount=computed(()=>jobs.value.filter(j=>active(j.status)).length)
const keyConfigured=computed(()=>{
  if(!config.value)return false
  return config.value.ai_provider==='openrouter'?Boolean(config.value.openrouter_key_configured):Boolean(config.value.gemini_key_configured)
})
const setupMissing=computed(()=>!config.value||!config.value.asr_available||!config.value.tools_available||!keyConfigured.value)
const engineMenu=ref<HTMLDetailsElement>()
function closeEngineMenu(){if(engineMenu.value){engineMenu.value.open=false;engineMenu.value.querySelector<HTMLElement>('summary')?.focus()}}
const page=ref('projects'),sourceUrl=ref(''),previewUrl=ref(''),busy=ref(false),initial=ref(true),offline=ref(false),dialog=ref<HTMLDialogElement>(),analysisDialog=ref<HTMLDialogElement>()
const selectedRevision=ref(''),mediaLoading=ref(false),analysis=ref<AnalysisView|null>(null),selection=ref<AnalysisSelection|null>(null)
let selectionWrite=Promise.resolve()
async function saveSelection(value:AnalysisSelection){const pid=project.value?.id;if(!pid)return;selectionWrite=selectionWrite.then(async()=>{try{const saved=await api.saveSelection(pid,value);if(project.value?.id===pid)selection.value=saved}catch(e){notify.error((e as Error).message)}})}
async function generateSelected(value:{analysis_hash:string;candidate_ids:string[]}){await selectionWrite;await start('render',value)}
const covers=ref<Record<string,string>>({}),trashDialog=ref<HTMLDialogElement>(),trashRows=ref<{id:string;name:string}[]>([]),trashKind=ref<'projects'|'cuts'>('projects')
const coverPending=new Set<string>()
async function loadCover(row:Project){if(!row.source||covers.value[row.id]||coverPending.has(row.id))return;coverPending.add(row.id);try{covers.value[row.id]=await api.media(row.id,'thumbnail')}catch{}finally{coverPending.delete(row.id)}}
async function deleteProject(id:string){const row=projects.value.find(p=>p.id===id);if(!confirm('Mover '+(row?.title||row?.name||'projeto')+' para a lixeira? O original será preservado.'))return;await action(async()=>{await api.deleteProject(id);if(project.value?.id===id){project.value=null;++generation};delete covers.value[id];await refresh()})}
async function deleteClip(id:string){if(!project.value||!confirm('Mover este corte para a lixeira? Ele deixará de participar das exportações.'))return;const pid=project.value.id;await action(async()=>{await api.deleteClip(pid,id);await openProject(pid)})}
async function bulkDelete(ids:string[]){if(!project.value||!confirm(`Mover ${ids.length} cortes para a lixeira?`))return;const pid=project.value.id;await action(async()=>{await api.bulkDeleteClips(pid,ids);await openProject(pid);notify.success('Cortes movidos para a lixeira.')})}
async function bulkExport(ids:string[]){if(!project.value)return;const pid=project.value.id;await action(async()=>{await api.bulkExportClips(pid,ids);await openProject(pid);notify.success('Cortes selecionados exportados.')})}
async function showTrash(kind:'projects'|'cuts'){await action(async()=>{trashKind.value=kind;trashRows.value=kind==='projects'?await api.trash():project.value?(await api.deletedClips(project.value.id)).map(r=>({id:r.revision_id,name:r.title})):[];trashDialog.value?.showModal()})}
async function restore(id:string){await action(async()=>{if(trashKind.value==='projects')await api.restoreProject(id);else if(project.value)await api.restoreClip(project.value.id,id);trashRows.value=trashRows.value.filter(r=>r.id!==id);await refresh();if(project.value)await openProject(project.value.id)})}

const newName=ref(''),sourceInput=ref(''),sourceKind=ref('file'),windowSeconds=ref(600)
const isYouTubeUrl=computed(()=>{if(sourceKind.value!=='url'||!sourceInput.value.trim())return true;return /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/i.test(sourceInput.value.trim())})
const reportJobs=createJobNotifier();let connectionFailed=false,connectionEpoch=0
let timer:ReturnType<typeof setInterval>|undefined;let refreshing=false;let generation=0
const projectJobs=computed(()=>jobs.value.filter(j=>j.project_id===project.value?.id)),running=computed(()=>jobs.value.some(j=>active(j.status)))
function navigate(destination:string){if(engineMenu.value)engineMenu.value.open=false;++generation;project.value=null;page.value=destination}
async function action(fn:()=>Promise<unknown>,success=''){if(busy.value)return;busy.value=true;try{await fn();if(success)notify.success(success)}catch(e){notify.error((e as Error).message)}finally{busy.value=false}}
async function refresh(){if(refreshing)return;refreshing=true;try{
  const [rows,tasks]=await Promise.all([api.projects(),api.jobs()]);projects.value=rows;for(const row of rows)void loadCover(row)
  const previous=jobs.value; jobs.value=tasks;reportJobs(tasks);offline.value=false;connectionFailed=false
  if(project.value){const latest=rows.find(p=>p.id===project.value?.id)
    const available=latest&&((!project.value.source&&!!latest.source)||(!project.value.has_transcript&&latest.has_transcript))
    if(latest)project.value=latest
    const finished=tasks.some(j=>j.project_id===project.value?.id&&['completed','failed','cancelled','interrupted'].includes(j.status)&&previous.find(p=>p.id===j.id)?.status!==j.status)
    if(finished||available)await openProject(project.value.id)
    else {const pid=project.value.id;const guard=generation;const [a,r]=await Promise.allSettled([api.analysis(pid),api.revisions(pid)]);if(project.value?.id===pid&&guard===generation){if(a.status==='fulfilled')analysis.value=a.value;if(r.status==='fulfilled')revisions.value=r.value}}
  }
}catch(e){offline.value=true;if(!connectionFailed)connectionEpoch++;connectionFailed=true;notify.error((e as Error).message,{key:'connection:'+connectionEpoch})}finally{refreshing=false}}
async function openProject(id:string){const same=project.value?.id===id;const prior=same?selectedRevision.value:'';const current=++generation;const detail=await api.project(id);if(current!==generation)return
  project.value=detail;page.value='projects';if(!same){transcript.value=null;revisions.value=[];sourceUrl.value='';previewUrl.value='';analysis.value=null;selection.value=null}
  mediaLoading.value=true
  const [t,r,s]=await Promise.allSettled([detail.has_transcript?api.transcript(id):Promise.resolve(null),api.revisions(id),detail.source?api.media(id,'source'):Promise.resolve('')])
  if(current!==generation)return
  transcript.value=t.status==='fulfilled'?t.value:null;revisions.value=r.status==='fulfilled'?r.value:[];sourceUrl.value=s.status==='fulfilled'?s.value:''
  if([t,r,s].some(item=>item.status==='rejected'))notify.warning('Alguns artefatos estão indisponíveis. O vídeo e a transcrição válidos continuam acessíveis.',{key:'artifacts:'+id})
  selectedRevision.value=revisions.value.some(row=>row.revision_id===prior)?prior:revisions.value[0]?.revision_id||''
  const [a,sel]=await Promise.allSettled([api.analysis(id),api.selection(id)]);if(current!==generation)return;if(a.status==='fulfilled')analysis.value=a.value;else notify.warning('Não foi possível carregar a análise salva.',{key:'analysis-load:'+id});if(sel.status==='fulfilled')selection.value=sel.value;else notify.warning('Não foi possível carregar a seleção de trechos.',{key:'selection-load:'+id})
  if(detail.is_manual){const url=await api.media(id,'manual').catch(()=> '');if(current===generation)previewUrl.value=url}
  else if(selectedRevision.value)await selectClip(selectedRevision.value)
  if(current===generation)mediaLoading.value=false
}
async function importProject(){await action(async()=>{const path=await api.pick('project');if(!path)return;const row=await api.importProject(path);await refresh();await openProject(row.id)})}
async function pickVideo(){await action(async()=>{const path=await api.pick('video');if(path){sourceInput.value=path;if(!newName.value)newName.value=path.split(/[\\/]/).pop()?.replace(/\.[^.]+$/,'')||'Novo projeto'}})}
async function create(){await action(async()=>{const value=await api.create(newName.value.trim(),sourceInput.value.trim(),{automatic:!setupMissing.value});dialog.value?.close();newName.value='';sourceInput.value='';await refresh();await openProject(value.project.id)})}
function showCreate(){newName.value='';sourceInput.value='';sourceKind.value='file';dialog.value?.showModal()}
function showAnalysis(){windowSeconds.value=config.value?.window_seconds||600;analysisDialog.value?.showModal()}
async function start(operation:string,options:Record<string,unknown>={}){await action(async()=>{if(!project.value)return;const queued=await api.start(project.value.id,operation,options);if(operation==='render')notify.info(`${queued.enqueued_items||0} prévia(s) enviada(s) · ${queued.ignored_ready||0} pronta(s) e ${queued.ignored_queued||0} já na fila, ignoradas.`);analysisDialog.value?.close();await refresh()},'Tarefa recebida. Acompanhe a fila do projeto.')}
async function review(decision:Decision){await action(async()=>{if(!project.value)return;await api.decide(project.value.id,decision);await openProject(project.value.id)},decision.decision==='approved'?'Corte aprovado para esta revisão.':'Corte rejeitado.')}
async function selectClip(id:string){if(!project.value)return;const pid=project.value.id;const current=generation;selectedRevision.value=id;previewUrl.value='';mediaLoading.value=true
  const url=await api.media(pid,id).catch(()=>{notify.error('Não foi possível abrir esta prévia.',{key:'preview:'+pid+':'+id});return ''})
  if(project.value?.id===pid&&current===generation&&selectedRevision.value===id){previewUrl.value=url;mediaLoading.value=false}
}
async function saveConfig(value:Config){config.value=await api.saveConfig(value)}
async function saveKey(key:string){const result=await api.saveKey(key);config.value=await api.config();return result}
async function saveOpenRouterKey(key:string){const result=await api.saveOpenRouterKey(key);config.value=await api.config();return result}
async function closeService(){await action(async()=>{await api.shutdown();if(timer)clearInterval(timer);offline.value=true;notify.info('Serviço encerrado. Abra novamente pelo atalho para continuar.')})}
async function openFolder(){await action(async()=>{if(project.value)await api.openFolder(project.value.id)})}
async function cancelJob(id:string){await action(async()=>{await api.cancel(id);await refresh()})}
async function replaceSource(id:string){await action(async()=>{const path=await api.pick('video');if(!path)return;await api.resume(id,{source_input:path});await refresh();notify.success('Arquivo selecionado. A preparação será retomada neste projeto.')})}
async function retryClip(value:{job_id:string;candidate_id:string}){await action(async()=>{await api.resume(value.job_id,{candidate_id:value.candidate_id});await refresh();notify.success('Corte enviado para a fila novamente.')})}
async function resumeJob(id:string){await action(async()=>{await api.resume(id);await refresh()})}
onMounted(async()=>{try{await Promise.all([refresh(),api.config().then(value=>config.value=value),api.systemProfile().then(res=>hardwareProfile.value=res.profile).catch(()=>{})])}catch(e){notify.error((e as Error).message)}finally{initial.value=false};timer=setInterval(refresh,3000)})
onUnmounted(()=>{if(timer)clearInterval(timer)})
</script>
<template>
  <el-config-provider :locale="ptBr" size="default" :z-index="2000">
    <div class="app-shell">
    <header class="global-header">
      <a class="brand" href="#" @click.prevent="navigate('projects')">
        <span class="brand-symbol"><Scissors :size="21"/></span>
        <span>AutoClip</span>
      </a>
      <nav class="global-navigation" aria-label="Navegação principal">
        <AppButton :class="{selected:page==='projects'}" @click="navigate('projects')">
          <Layers :size="17"/>Projetos<span>{{projects.length}}</span>
        </AppButton>
        <AppButton :class="{selected:page==='settings'}" @click="navigate('settings')">
          <Settings2 :size="17"/>Configurações
        </AppButton>
      </nav>
      <div class="global-actions">
        <AppButton class="header-queue-btn button secondary small" :class="{active:activeJobsCount>0}" title="Fila global de tarefas" @click="showGlobalQueue=true">
          <ListOrdered :size="15"/>Fila<span v-if="activeJobsCount" class="header-queue-badge">{{activeJobsCount}}</span>
        </AppButton>
        <AppButton class="button secondary small header-import-action" @click="importProject" :disabled="busy||initial"><FolderOpen :size="15"/>Importar projeto</AppButton>
        <AppButton class="button primary small new-project-action" @click="showCreate" :disabled="busy||initial"><Plus :size="15"/>Novo projeto</AppButton>
        <details ref="engineMenu" class="engine-menu" @keydown.esc.prevent="closeEngineMenu">
          <summary>
            <span class="local-dot" :class="{offline}"></span>
            {{offline?'Sem conexão':'Motor local'}}
            <HardDrive :size="15"/>
          </summary>
          <div class="engine-popover">
            <div class="sidebar-session">
              <strong>Sessão local</strong>
              <span class="session-info">
                <span class="local-dot" :class="{offline}"></span>
                {{offline?'Sem conexão':'Conectado neste computador'}}
                <AppButton class="icon-button" title="Atualizar projetos" @click="action(refresh)">
                  <RefreshCw :size="15"/>
                </AppButton>
              </span>
            </div>
            <p>{{jobs.filter(j=>j.status==='running').length}} tarefa(s) em execução · {{jobs.filter(j=>j.status==='pending').length}} na fila.</p>
            <p>Transcrição e renderização em CPU.<br/>Seus arquivos ficam neste computador.</p>
            <AppButton class="button small secondary" @click="closeService" :disabled="busy||running" title="Disponível quando nenhuma tarefa estiver em execução">
              Encerrar serviço
            </AppButton>
          </div>
        </details>
      </div>
    </header>

    <main class="main-content">
      <div class="page-content">
        <div v-if="initial" class="loading-state">
          <LoaderCircle class="spin" :size="25"/>
          <p>Abrindo seus projetos…</p>
        </div>
        <template v-else>
          <!-- Painel Proeminente de Prontidão e Onboarding -->
          <section v-if="setupMissing&&!project&&page==='projects'" class="readiness-panel studio-readiness-panel">
            <div class="readiness-info">
              <span class="readiness-tag"><Sparkles :size="13"/>Configuração do Estúdio AutoClip</span>
              <h2>Prepare seu espaço de edição</h2>
              <p>Confira os recursos necessários antes de iniciar o processamento automático local.</p>
              <div class="readiness-items">
                <span :class="{ready:config?.asr_available}">
                  <Check v-if="config?.asr_available" :size="13"/>
                  <AlertTriangle v-else :size="13"/>
                  {{config?.asr_available?'Transcrição disponível (Whisper local)':'Localizar modelo Whisper'}}
                </span>
                <span :class="{ready:config?.tools_available}">
                  <Check v-if="config?.tools_available" :size="13"/>
                  <AlertTriangle v-else :size="13"/>
                  {{config?.tools_available?'Processamento de vídeo pronto (FFmpeg)':'Localizar FFmpeg e ffprobe'}}
                </span>
                <span :class="{ready:keyConfigured}">
                  <Check v-if="keyConfigured" :size="13"/>
                  <AlertTriangle v-else :size="13"/>
                  {{keyConfigured?(config?.ai_provider==='openrouter'?'Chave OpenRouter configurada':'Chave Gemini configurada'):(config?.ai_provider==='openrouter'?'Adicionar chave OpenRouter':'Adicionar chave Gemini')}}
                </span>
              </div>
            </div>
            <AppButton class="button primary" @click="navigate('settings')">Configurar processamento</AppButton>
          </section>

          <Transition name="screen">
            <div :key="project?.id||page" class="screen-content">
              <SettingsPanel
                v-if="page==='settings'&&config"
                :config="config"
                :save-config="saveConfig"
                :save-key="saveKey"
                :save-open-router-key="saveOpenRouterKey"
                :get-connection="api.geminiConnection"
                :test-connection="api.testGemini"
                :pick="api.pick"
              />
              <ProjectWorkspace
                v-else-if="project"
                :key="project.id"
                :project="project"
                :transcript="transcript"
                :revisions="revisions"
                :jobs="projectJobs"
                :source-url="sourceUrl"
                :preview-url="previewUrl"
                :selected-revision="selectedRevision"
                :media-loading="mediaLoading"
                :busy="busy"
                :analysis="analysis"
                :selection="selection"
                @selection="saveSelection"
                @back="navigate('projects')"
                @folder="openFolder"
                @transcribe="start('transcribe')"
                @analyze="showAnalysis"
                @resume-analysis="start('analyze')"
                @render="generateSelected"
                @cancel="cancelJob($event)"
                @retry="retryClip"
                @resume="resumeJob($event)"
                @replace-source="replaceSource($event)"
                @select="selectClip"
                @decision="review"
                @export="start('export')"
                @bulk-delete="bulkDelete"
                @bulk-export="bulkExport"
                @delete="deleteClip"
                @deleted="showTrash('cuts')"
              />
              <ProjectLibrary
                v-else
                :covers="covers"
                :projects="projects"
                :busy="busy"
                :active-projects="jobs.filter(j=>active(j.status)).map(j=>j.project_id)"
                @open="action(()=>openProject($event))"
                @create="showCreate"
                @import="importProject"
                @delete="deleteProject"
                @trash="showTrash('projects')"
                @queue="showGlobalQueue=true"
              />
            </div>
          </Transition>
        </template>
      </div>
    </main>
  </div>

  <GlobalQueueModal
    v-if="showGlobalQueue"
    :jobs="jobs"
    :projects="projects"
    :busy="busy"
    @cancel="cancelJob"
    @open="action(()=>openProject($event));showGlobalQueue=false"
    @close="showGlobalQueue=false"
  />

  <!-- CENTRO DE IMPORTAÇÃO E CRIAÇÃO DE PROJETOS DO ESTÚDIO -->
  <dialog ref="dialog" class="modal studio-dialog">
    <form @submit.prevent="create" class="studio-import-form">
      <header class="studio-dialog-header">
        <div class="studio-dialog-title-wrap">
          <span class="dialog-eyebrow"><Scissors :size="13"/>Estúdio de Criação</span>
          <h2>Novo projeto</h2>
          <p>Comece com um vídeo. O original será preservado.</p>
        </div>
        <AppButton type="button" class="icon-button modal-close-btn" title="Fechar" @click="dialog?.close()">
          <X :size="19"/>
        </AppButton>
      </header>

      <!-- Alternador de Fonte de Vídeo -->
      <div class="source-switch" role="radiogroup" aria-label="Fonte do vídeo">
        <AppButton
          type="button"
          :class="{selected:sourceKind==='file'}"
          role="radio"
          :aria-checked="sourceKind==='file'"
          @click="sourceKind='file';sourceInput=''"
        >
          <FileVideo :size="17"/>Arquivo local
        </AppButton>
        <AppButton
          type="button"
          :class="{selected:sourceKind==='url'}"
          role="radio"
          :aria-checked="sourceKind==='url'"
          @click="sourceKind='url';sourceInput=''"
        >
          <Link :size="17"/>Link do YouTube
        </AppButton>
      </div>

      <!-- Área de Origem: Arquivo Local -->
      <div v-if="sourceKind==='file'" class="file-drop studio-file-drop">
        <div v-if="sourceInput" class="selected-file-card">
          <div class="file-icon-badge"><FileVideo :size="28"/></div>
          <div class="file-info-col">
            <strong>{{sourceInput.split(/[\\/]/).pop()}}</strong>
            <small class="file-path-text" :title="sourceInput">{{sourceInput}}</small>
            <span class="status-pill ready-pill" data-status="ready"><i></i>Vídeo pronto para importação</span>
          </div>
          <AppButton type="button" class="button small secondary" :disabled="busy" @click="pickVideo">
            <FolderOpen :size="14"/>Trocar vídeo
          </AppButton>
        </div>
        <div v-else class="drop-prompt">
          <div class="drop-icon-wrap"><FileVideo :size="34"/></div>
          <strong>Escolha um vídeo do seu computador</strong>
          <p>Formatos recomendados: MP4, MOV, MKV ou WebM (HD / 4K)</p>
          <AppButton type="button" class="button secondary pick-video-btn" :disabled="busy" @click="pickVideo">
            <FolderOpen :size="16"/>Selecionar vídeo
          </AppButton>
        </div>
      </div>

      <!-- Área de Origem: Link do YouTube -->
      <div v-else class="url-input-container">
        <label class="field url-field">URL do vídeo
          <div class="url-field-wrapper">
            <Link :size="16" class="url-field-icon"/>
            <input type="url" v-model="sourceInput" placeholder="https://www.youtube.com/watch?v=..." required/>
          </div>
          <small v-if="!isYouTubeUrl" style="color:var(--color-warning-text,#f59e0b);font-weight:500">
            Aviso: O link informado parece não ser do YouTube (youtube.com ou youtu.be).
          </small>
          <small v-else-if="sourceInput.trim()" style="color:#10b981;font-weight:500">
            ✓ Link do YouTube reconhecido. O vídeo e o áudio serão baixados com qualidade original.
          </small>
          <small v-else>Use conteúdo autorizado para processamento.</small>
        </label>
      </div>

      <!-- Nome do Projeto -->
      <label class="field project-name-field">Nome do projeto
        <input v-model="newName" placeholder="Ex.: Entrevista sobre educação" maxlength="100" required/>
        <small>Identificador do projeto na sua biblioteca local.</small>
      </label>

      <!-- Resumo do Fluxo e Parâmetros da IA -->
      <div class="analysis-summary studio-pipeline-card">
        <div class="summary-pipeline-header">
          <Sparkles :size="15"/>
          <strong>{{setupMissing?'Importar vídeo · concluir configuração depois':'Importar → Transcrever → Analisar'}}</strong>
        </div>
        <div class="summary-details">
          <span>{{(config?.ai_provider==='openrouter'?config?.openrouter_model:config?.gemini_model)||'Modelo de IA'}} · preferência {{config?.clip_preferred_seconds||60}} s · máximo {{config?.clip_max_seconds||180}} s</span>
          <span>Geração de prévias manual · {{config?.pause_mode==='preserve'?'pausas preservadas':'redução conservadora de pausas'}}</span>
        </div>
      </div>

      <p v-if="!setupMissing" class="subtle pipeline-cost-notice">
        {{config?.ai_provider==='openrouter'?'A transcrição será analisada automaticamente pelo OpenRouter. As chamadas são dimensionadas pelo conteúdo.':'A transcrição será analisada automaticamente pelo Gemini. As chamadas são dimensionadas pelo conteúdo; a API pode gerar custos.'}}
      </p>

      <div v-if="setupMissing" class="readiness-items studio-setup-warning">
        <span>Configuração incompleta para o processamento automático.</span>
        <AppButton type="button" class="button secondary" @click="dialog?.close();navigate('settings')">
          Abrir configurações
        </AppButton>
      </div>

      <!-- Rodapé com Ações -->
      <footer class="studio-dialog-footer">
        <AppButton type="button" class="button secondary" @click="dialog?.close()">Cancelar</AppButton>
        <AppButton class="button primary studio-submit-btn" :disabled="busy||!sourceInput.trim()||!newName.trim()||!config?.tools_available||(sourceKind==='url'&&!isYouTubeUrl)">
          <LoaderCircle v-if="busy" class="spin" :size="16"/>
          {{setupMissing?'Importar vídeo':'Criar projeto'}}
        </AppButton>
      </footer>
    </form>
  </dialog>

  <!-- LIXEIRA -->
  <dialog ref="trashDialog" class="modal">
    <div class="trash-content">
      <header>
        <h2>{{trashKind==='projects'?'Lixeira de projetos':'Lixeira de cortes'}}</h2>
        <AppButton class="icon-button" title="Fechar lixeira" @click="trashDialog?.close()"><X :size="19"/></AppButton>
      </header>
      <p class="subtle">Arquivos preservados. Restaure para voltar a usar.</p>
      <p v-if="!trashRows.length">A lixeira está vazia.</p>
      <div v-for="row in trashRows" :key="row.id" class="trash-row">
        <strong>{{row.name}}</strong>
        <AppButton class="button small secondary" :disabled="busy||running" @click="restore(row.id)">Restaurar</AppButton>
      </div>
    </div>
  </dialog>

  <!-- MODAL DE ANÁLISE DE IA -->
  <dialog ref="analysisDialog" class="modal">
    <form @submit.prevent="start('analyze',{window_seconds:windowSeconds,max_text_chars:config?.max_text_chars||60000})">
      <header>
        <div>
          <h2>Analisar com {{config?.ai_provider==='openrouter'?'OpenRouter':'Gemini'}}</h2>
          <p>O motor organiza as chamadas para analisar toda a transcrição.</p>
        </div>
        <AppButton type="button" class="icon-button" title="Fechar" @click="analysisDialog?.close()"><X :size="19"/></AppButton>
      </header>
      <div class="analysis-summary">
        <strong>{{config?.ai_provider==='openrouter'?config?.openrouter_model:config?.gemini_model}}</strong>
        <span>Preferência {{config?.clip_preferred_seconds||60}} s · máximo {{config?.clip_max_seconds||180}} s · {{config?.show_thought_summaries===false?'resumos desativados':'resumos da API quando disponíveis'}}</span>
        <span>{{project?.word_count.toLocaleString('pt-BR')}} palavras disponíveis</span>
      </div>
      <details class="analysis-advanced">
        <summary>Ajustes avançados</summary>
        <label class="field">Janela em segundos
          <input type="number" v-model.number="windowSeconds" min="60" max="1800" required/>
          <small>Quantidade de transcrição por solicitação. Pode manter o padrão; não define o tamanho dos cortes.</small>
        </label>
      </details>
      <p class="subtle">A transcrição em texto será enviada ao {{config?.ai_provider==='openrouter'?'OpenRouter':'Gemini'}}. Chamadas automáticas conforme o conteúdo, com novas tentativas para falhas recuperáveis. Você pode cancelar; a API pode gerar custos.</p>
      <div v-if="!keyConfigured" class="subtle">Configure sua chave {{config?.ai_provider==='openrouter'?'OpenRouter':'Gemini'}} nas configurações primeiro.</div>
      <footer>
        <AppButton type="button" class="button secondary" @click="analysisDialog?.close()">Cancelar</AppButton>
        <AppButton class="button primary" :disabled="busy||!keyConfigured">Iniciar análise</AppButton>
      </footer>
    </form>
  </dialog>

  <OnboardingModal
    v-if="showOnboarding"
    :profile="hardwareProfile"
    :tools-missing="!config?.tools_available"
    :asr-missing="!config?.asr_available"
    :gemini-key-configured="Boolean(config?.gemini_key_configured)"
    :openrouter-key-configured="Boolean(config?.openrouter_key_configured)"
    @close="onboardingDismissed = true"
    @configured="onDependenciesConfigured"
    @save-key="saveKey"
    @save-open-router-key="saveOpenRouterKey"
  />
  </el-config-provider>
</template>

<style scoped>
.studio-readiness-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(217, 119, 36, 0.06) 100%);
  border: 1px solid var(--color-border-subtle, var(--line));
  border-left: 4px solid var(--color-accent, var(--accent));
  border-radius: 14px;
  padding: 20px 24px;
  margin-bottom: 24px;
}

.readiness-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.readiness-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-accent, var(--accent));
}

.readiness-info h2 {
  font-size: 1.15rem;
  margin: 0;
  color: var(--color-text-primary, var(--ink));
}

.readiness-info p {
  font-size: 0.85rem;
  color: var(--color-text-secondary, var(--muted));
  margin: 0;
}

.readiness-items {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 6px;
}

.readiness-items span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
  padding: 5px 10px;
  border-radius: 6px;
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  color: var(--color-text-secondary, var(--muted));
}

.readiness-items span.ready {
  color: #10b981;
  border-color: rgba(16, 185, 129, 0.3);
  background: rgba(16, 185, 129, 0.06);
}

.studio-dialog {
  width: min(640px, 94vw);
  max-width: 640px;
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: 18px;
  background: var(--color-surface, var(--panel));
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.45);
  padding: 0;
  overflow: hidden;
}

.studio-import-form {
  display: flex;
  flex-direction: column;
  padding: 24px;
  gap: 18px;
}

.studio-dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--color-border-subtle, var(--line));
}

.dialog-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-accent, var(--accent));
  margin-bottom: 4px;
}

.studio-dialog-header h2 {
  font-size: 1.25rem;
  margin: 0;
  color: var(--color-text-primary, var(--ink));
}

.studio-dialog-header p {
  font-size: 0.82rem;
  color: var(--color-text-secondary, var(--muted));
  margin: 2px 0 0;
}

.source-switch {
  display: flex;
  gap: 8px;
  background: var(--color-surface-hover, var(--soft));
  padding: 4px;
  border-radius: 10px;
  border: 1px solid var(--color-border-subtle, var(--line));
}

.source-switch button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 14px;
  font-size: 0.85rem;
  font-weight: 500;
  border-radius: 8px;
  border: 0;
  background: transparent;
  color: var(--color-text-secondary, var(--muted));
  transition: all 0.15s ease;
}

.source-switch button.selected {
  background: var(--color-surface, var(--panel));
  color: var(--color-accent, var(--accent));
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}

.studio-file-drop {
  border: 1px dashed var(--color-border-subtle, #3b4252);
  border-radius: 12px;
  background: var(--color-surface-hover, var(--soft));
  padding: 20px;
  text-align: center;
  transition: border-color 0.15s ease;
}

.studio-file-drop:hover {
  border-color: var(--color-accent, var(--accent));
}

.drop-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.drop-icon-wrap {
  width: 54px;
  height: 54px;
  border-radius: 14px;
  background: rgba(99, 102, 241, 0.1);
  color: var(--color-accent, var(--accent));
  display: grid;
  place-items: center;
  margin-bottom: 4px;
}

.drop-prompt strong {
  font-size: 0.95rem;
  color: var(--color-text-primary, var(--ink));
}

.drop-prompt p {
  font-size: 0.78rem;
  color: var(--color-text-muted, var(--muted));
  margin: 0 0 8px;
}

.selected-file-card {
  display: flex;
  align-items: center;
  gap: 14px;
  text-align: left;
}

.file-icon-badge {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.file-info-col {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.file-info-col strong {
  font-size: 0.9rem;
  color: var(--color-text-primary, var(--ink));
  word-break: break-all;
}

.file-path-text {
  font-size: 0.72rem;
  color: var(--color-text-muted, var(--muted));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 340px;
}

.ready-pill {
  width: fit-content;
  margin-top: 4px;
  font-size: 0.72rem;
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
  border-color: rgba(16, 185, 129, 0.3);
}

.url-input-container {
  display: flex;
  flex-direction: column;
}

.url-field-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  margin-top: 6px;
}

.url-field-icon {
  position: absolute;
  left: 12px;
  color: var(--color-text-muted, var(--muted));
  pointer-events: none;
}

.url-field-wrapper input {
  width: 100%;
  padding-left: 36px;
}

.project-name-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.project-name-field input {
  padding: 10px 14px;
  border-radius: 8px;
}

.studio-pipeline-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px 16px;
  background: var(--color-surface-hover, var(--soft));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: 10px;
}

.summary-pipeline-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-accent, var(--accent));
  font-size: 0.85rem;
}

.summary-details {
  display: flex;
  flex-direction: column;
  gap: 3px;
  font-size: 0.78rem;
  color: var(--color-text-secondary, var(--muted));
}

.pipeline-cost-notice {
  font-size: 0.75rem;
  margin: -4px 0 0;
  line-height: 1.4;
}

.studio-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 14px;
  border-top: 1px solid var(--color-border-subtle, var(--line));
}

.studio-submit-btn {
  font-weight: 600;
  padding: 9px 20px;
}
</style>
