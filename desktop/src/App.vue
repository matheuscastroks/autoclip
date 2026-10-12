<script setup lang="ts">
import {computed,onMounted,onUnmounted,ref} from 'vue'
import {Scissors,Layers,Settings2,HardDrive,Plus,ArrowUpRight,FileVideo,Link,FolderOpen,X,RefreshCw,LoaderCircle,Info} from '@lucide/vue'
import {api} from './api'
import type {Project,Config,Job,Transcript,Revision,Decision} from './types'
import {active} from './format'
import ProjectLibrary from './components/ProjectLibrary.vue'
import ProjectWorkspace from './components/ProjectWorkspace.vue'
import SettingsPanel from './components/SettingsPanel.vue'
const projects=ref<Project[]>([]),config=ref<Config|null>(null),jobs=ref<Job[]>([]),project=ref<Project|null>(null),transcript=ref<Transcript|null>(null),revisions=ref<Revision[]>([])
const page=ref('projects'),sourceUrl=ref(''),previewUrl=ref(''),busy=ref(false),initial=ref(true),failure=ref(''),message=ref(''),dialog=ref<HTMLDialogElement>(),analysisDialog=ref<HTMLDialogElement>()
const selectedRevision=ref(''),mediaLoading=ref(false)
const newName=ref(''),sourceInput=ref(''),sourceKind=ref('file'),callLimit=ref(10),windowSeconds=ref(600),textAuthorized=ref(false)
let timer:ReturnType<typeof setInterval>|undefined;let refreshing=false;let generation=0
const projectJobs=computed(()=>jobs.value.filter(j=>j.project_id===project.value?.id)),running=computed(()=>jobs.value.some(j=>active(j.status)))
const minimumWindows=computed(()=>Math.ceil((project.value?.duration_us||0)/1e6/Math.max(1,windowSeconds.value-30)))
async function action(fn:()=>Promise<unknown>,success=''){if(busy.value)return;busy.value=true;failure.value='';message.value='';try{await fn();if(success)message.value=success}catch(e){failure.value=(e as Error).message}finally{busy.value=false}}
async function refresh(){if(refreshing)return;refreshing=true;try{
  const [rows,tasks]=await Promise.all([api.projects(),api.jobs()]);projects.value=rows
  const previous=jobs.value; jobs.value=tasks
  if(project.value){const latest=rows.find(p=>p.id===project.value?.id);if(latest)project.value=latest
    const finished=tasks.some(j=>j.project_id===project.value?.id&&j.status==='completed'&&previous.find(p=>p.id===j.id)?.status!=='completed')
    if(finished)await openProject(project.value.id)
  }
}catch(e){failure.value=(e as Error).message}finally{refreshing=false}}
async function openProject(id:string){const prior=project.value?.id===id?selectedRevision.value:'';const current=++generation;const detail=await api.project(id);if(current!==generation)return
  project.value=detail;page.value='projects';transcript.value=null;revisions.value=[];sourceUrl.value='';previewUrl.value=''
  mediaLoading.value=true
  const [t,r,s]=await Promise.allSettled([detail.has_transcript?api.transcript(id):Promise.resolve(null),api.revisions(id),detail.source?api.media(id,'source'):Promise.resolve('')])
  if(current!==generation)return
  transcript.value=t.status==='fulfilled'?t.value:null;revisions.value=r.status==='fulfilled'?r.value:[];sourceUrl.value=s.status==='fulfilled'?s.value:''
  if([t,r,s].some(item=>item.status==='rejected'))failure.value='Alguns artefatos estão indisponíveis. O vídeo e a transcrição válidos continuam acessíveis.'
  selectedRevision.value=revisions.value.some(row=>row.revision_id===prior)?prior:revisions.value[0]?.revision_id||''
  if(detail.is_manual){const url=await api.media(id,'manual').catch(()=> '');if(current===generation)previewUrl.value=url}
  else if(selectedRevision.value)await selectClip(selectedRevision.value)
  if(current===generation)mediaLoading.value=false
}
async function importProject(){await action(async()=>{const path=await api.pick('project');if(!path)return;const row=await api.importProject(path);await refresh();await openProject(row.id)})}
async function pickVideo(){await action(async()=>{const path=await api.pick('video');if(path){sourceInput.value=path;if(!newName.value)newName.value=path.split(/[\\/]/).pop()?.replace(/\.[^.]+$/,'')||'Novo projeto'}})}
async function create(){await action(async()=>{const value=await api.create(newName.value.trim(),sourceInput.value.trim());dialog.value?.close();newName.value='';sourceInput.value='';await refresh();await openProject(value.project.id)})}
function showCreate(){newName.value='';sourceInput.value='';sourceKind.value='file';dialog.value?.showModal()}
function showAnalysis(){callLimit.value=config.value?.max_calls||10;windowSeconds.value=config.value?.window_seconds||600;textAuthorized.value=false;analysisDialog.value?.showModal()}
async function start(operation:string,options:Record<string,unknown>={}){await action(async()=>{if(!project.value)return;await api.start(project.value.id,operation,options);analysisDialog.value?.close();await refresh()},'Tarefa iniciada. Você pode acompanhar abaixo.')}
async function review(decision:Decision){await action(async()=>{if(!project.value)return;await api.decide(project.value.id,decision);await openProject(project.value.id)},decision.decision==='approved'?'Corte aprovado para esta revisão.':'Corte rejeitado.')}
async function selectClip(id:string){if(!project.value)return;const pid=project.value.id;const current=generation;selectedRevision.value=id;previewUrl.value='';mediaLoading.value=true
  const url=await api.media(pid,id).catch(()=> '')
  if(project.value?.id===pid&&current===generation&&selectedRevision.value===id){previewUrl.value=url;mediaLoading.value=false}
}
async function saveConfig(value:Config){config.value=await api.saveConfig(value)}
async function saveKey(key:string){await api.saveKey(key);config.value=await api.config()}
async function closeService(){await action(async()=>{await api.shutdown();if(timer)clearInterval(timer);failure.value='Serviço encerrado. Abra novamente pelo atalho para continuar.'})}
async function openFolder(){await action(async()=>{if(project.value)await api.openFolder(project.value.id)})}
async function cancelJob(id:string){await action(async()=>{await api.cancel(id);await refresh()})}
async function resumeJob(id:string){await action(async()=>{await api.resume(id);await refresh()})}
onMounted(async()=>{try{await Promise.all([refresh(),api.config().then(value=>config.value=value)])}catch(e){failure.value=(e as Error).message}finally{initial.value=false};timer=setInterval(refresh,3000)})
onUnmounted(()=>{if(timer)clearInterval(timer)})
</script>
<template>
  <div class="app-shell"><aside class="sidebar"><a class="brand" href="#" @click.prevent="project=null;page='projects'"><span class="brand-symbol"><Scissors :size="23"/></span><span>AutoClip<small>Seu espaço de edição</small></span></a><button class="sidebar-create" @click="showCreate" :disabled="busy||initial||running"><Plus :size="17"/>Novo projeto</button><nav aria-label="Navegação principal"><button :class="{selected:page==='projects'}" @click="page='projects';project=null"><Layers :size="19"/>Projetos<span>{{projects.length}}</span></button><button :class="{selected:page==='settings'}" @click="page='settings';project=null"><Settings2 :size="19"/>Configurações</button></nav><div class="sidebar-bottom"><div class="engine-status"><span class="local-dot" :class="{offline:!!failure}"></span><div><strong>Motor local</strong><small>Transcrição e render em CPU</small></div><HardDrive :size="16"/></div><p>Seus arquivos, no seu computador.</p><button class="text-button" @click="closeService" :disabled="busy||running" title="Disponível quando nenhuma tarefa estiver em execução">Encerrar serviço</button></div></aside>
    <main class="main-content"><div class="topbar"><span class="app-context">{{project?'Área de trabalho':page==='settings'?'Preferências':'Área de trabalho'}}</span><span class="session-info"><span class="local-dot"></span>Sessão local<button class="icon-button" title="Atualizar projetos" @click="action(refresh)"><RefreshCw :size="15"/></button></span></div><div class="page-content"><div v-if="failure" class="notice error" role="alert"><Info :size="18"/><span>{{failure}}</span><button class="icon-button" title="Fechar aviso" @click="failure=''"><X :size="17"/></button></div><div v-if="message" class="notice success" role="status">{{message}}<button class="icon-button" title="Fechar aviso" @click="message=''"><X :size="17"/></button></div><div v-if="initial" class="loading-state"><LoaderCircle class="spin" :size="25"/><p>Abrindo seus projetos…</p></div><template v-else><SettingsPanel v-if="page==='settings'&&config" :config="config" :save-config="saveConfig" :save-key="saveKey" :pick="api.pick"/><ProjectWorkspace v-else-if="project" :key="project.id" :project="project" :transcript="transcript" :revisions="revisions" :jobs="projectJobs" :source-url="sourceUrl" :preview-url="previewUrl" :selected-revision="selectedRevision" :media-loading="mediaLoading" :busy="busy||running" @back="project=null" @folder="openFolder" @transcribe="start('transcribe')" @analyze="showAnalysis" @render="start('render')" @cancel="cancelJob($event)" @resume="resumeJob($event)" @select="selectClip" @decision="review" @export="start('export')"/><ProjectLibrary v-else :projects="projects" :busy="busy||running" @open="action(()=>openProject($event))" @create="showCreate" @import="importProject"/></template></div></main>
  </div>
  <dialog ref="dialog" class="modal"><form @submit.prevent="create"><header><div><h2>Novo projeto</h2><p>Comece com um vídeo. O original será preservado.</p></div><button type="button" class="icon-button" title="Fechar" @click="dialog?.close()"><X :size="19"/></button></header><div class="source-switch"><button type="button" :class="{selected:sourceKind==='file'}" @click="sourceKind='file';sourceInput=''"><FileVideo :size="17"/>Arquivo local</button><button type="button" :class="{selected:sourceKind==='url'}" @click="sourceKind='url';sourceInput=''"><Link :size="17"/>Link do YouTube</button></div><div v-if="sourceKind==='file'" class="file-drop"><FileVideo :size="32"/><p>{{sourceInput?sourceInput.split(/[\\/]/).pop():'Escolha um vídeo do seu computador'}}</p><button type="button" class="button secondary" :disabled="busy" @click="pickVideo"><FolderOpen :size="16"/>Selecionar vídeo</button></div><label v-else class="field">URL do vídeo<input type="url" v-model="sourceInput" placeholder="https://www.youtube.com/watch?v=..." required/><small>Use conteúdo autorizado para processamento.</small></label><label class="field">Nome do projeto<input v-model="newName" placeholder="Ex.: Entrevista sobre educação" maxlength="100" required/></label><p class="subtle">Importar não inicia a transcrição nem a análise com IA.</p><p v-if="failure" class="notice error">{{failure}}</p><footer><button type="button" class="button secondary" @click="dialog?.close()">Cancelar</button><button class="button primary" :disabled="busy||!sourceInput.trim()||!newName.trim()"><LoaderCircle v-if="busy" class="spin" :size="16"/>Criar projeto</button></footer></form></dialog>
  <dialog ref="analysisDialog" class="modal"><form @submit.prevent="start('analyze',{authorize_text:true,max_calls:callLimit,window_seconds:windowSeconds,max_text_chars:config?.max_text_chars||60000})"><header><div><h2>Analisar com Gemini</h2><p>Revise o orçamento antes de iniciar.</p></div><button type="button" class="icon-button" title="Fechar" @click="analysisDialog?.close()"><X :size="19"/></button></header><div class="analysis-summary"><strong>{{config?.gemini_model}}</strong><span>{{project?.word_count.toLocaleString('pt-BR')}} palavras disponíveis</span></div><div class="field-pair"><label class="field">Limite de tentativas<input type="number" v-model.number="callLimit" min="1" max="100" required/></label><label class="field">Janela em segundos<input type="number" v-model.number="windowSeconds" min="60" max="1800" required/></label></div><p class="subtle">Estimativa inicial: {{minimumWindows}} janela(s). O motor confere o número real antes de enviar. Retries e reparação de JSON entram no limite.</p><label class="check-row authorization"><input type="checkbox" v-model="textAuthorized"/><span>Autorizo o envio da transcrição em texto para este trabalho, até o limite informado. A API pode gerar custos.</span></label><div v-if="!config?.gemini_key_configured" class="notice">Configure sua chave Gemini nas configurações primeiro.</div><p v-if="failure" class="notice error">{{failure}}</p><footer><button type="button" class="button secondary" @click="analysisDialog?.close()">Cancelar</button><button class="button primary" :disabled="busy||!textAuthorized||!config?.gemini_key_configured||running">Iniciar análise</button></footer></form></dialog>
</template>
