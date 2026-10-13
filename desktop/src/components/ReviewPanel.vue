<script setup lang="ts">
import AppButton from './AppButton.vue'
import {computed,ref,watch} from 'vue'
import {Scissors,Info,Download,Trash2,Share2,Check,Clock,Film,Copy} from '@lucide/vue'
import type {Revision,Checks,Decision,Job} from '../types'
import {notify} from '../notifications'
import {time,labels} from '../format'
import {active} from '../format'

const props=defineProps<{revisions:Revision[];manual:boolean;mediaUrl:string;sourceUrl:string;busy?:boolean;selectedRevision?:string;mediaLoading?:boolean;processing?:boolean;jobs?:Job[]}>()
const emit=defineEmits<{select:[id:string];decision:[value:Decision];export:[];delete:[id:string];deleted:[];resume:[id:string];bulkDelete:[ids:string[]];bulkExport:[ids:string[]]}>()

const filter=ref('all')
const deleteBlockedReason=computed(()=>props.busy?'Aguarde a operação atual.':(props.jobs||[]).some(j=>active(j.status)&&!['transcribe','analyze'].includes(j.operation))?'Aguarde ou cancele a geração, exportação ou importação para excluir este corte.':!props.jobs&&props.processing?'Aguarde o processamento para excluir este corte.':'')
const visible=computed(()=>props.revisions.filter(r=>filter.value==='all'||filter.value==='approved'&&r.technical_pass||filter.value==='review'&&r.review_status==='needs_review'||filter.value==='exported'&&r.exported))
const bulk=ref<string[]>([])
const allVisible=computed(()=>visible.value.length>0&&visible.value.every(r=>bulk.value.includes(r.revision_id)))
const exportableBulk=computed(()=>bulk.value.length>0&&bulk.value.every(id=>props.revisions.some(r=>r.revision_id===id&&r.technical_pass)))

watch(()=>props.revisions,rows=>{bulk.value=bulk.value.filter(id=>rows.some(r=>r.revision_id===id))})
function toggleAll(){const ids=visible.value.map(r=>r.revision_id);bulk.value=allVisible.value?bulk.value.filter(id=>!ids.includes(id)):[...new Set([...bulk.value,...ids])]}

const selected=ref('')
watch(()=>props.selectedRevision,id=>{if(id&&props.revisions.some(r=>r.revision_id===id)&&!visible.value.some(r=>r.revision_id===id))filter.value='all'},{flush:'sync'})
const current=computed(()=>visible.value.find(r=>r.revision_id===(props.selectedRevision||selected.value))||visible.value[0])
watch(visible,rows=>{if(props.selectedRevision&&rows.some(r=>r.revision_id===props.selectedRevision)){selected.value=props.selectedRevision;return}if(!rows.some(r=>r.revision_id===selected.value)&&rows.length){selected.value=rows[0].revision_id;emit('select',selected.value)}},{immediate:true})
watch(current,value=>{if(value&&!value.technical_pass)notify.error('A verificação técnica falhou. Gere a prévia novamente.',{key:'revision:'+value.revision_id+':'+value.content_hash})},{immediate:true})

function choose(id:string){selected.value=id;emit('select',id)}

function copyDescription(){
  if(current.value?.description){
    navigator.clipboard.writeText(current.value.description).then(()=>{
      notify.success('Descrição copiada para a área de transferência.')
    }).catch(()=>{})
  }
}
</script>

<template>
  <div v-if="manual" class="manual-review">
    <div class="subtle">
      <Info :size="19"/>
      <div>
        <strong>Prévia manual de renderização</strong>
        <p>Este trecho é um teste técnico. Não foi selecionado pelo Gemini e não está aprovado editorialmente.</p>
      </div>
    </div>
    <video v-if="mediaUrl" class="manual-player" :src="mediaUrl" controls preload="metadata" playsinline></video>
  </div>

  <div v-if="!manual&&!revisions.length" class="empty-state cuts-empty">
    <span class="empty-icon"><Scissors :size="32"/></span>
    <h2>Nenhum corte disponível</h2>
    <p>A transcrição pode ser consultada. Na aba Análise, escolha propostas e gere prévias. Cada prévia aparece aqui após a verificação técnica.</p>
    <span class="subtle">Os cortes ficam disponíveis após a validação técnica.</span>
  </div>

  <div v-if="!manual&&revisions.length" class="cuts-review-layout">
    <div class="cuts-review-left">
      <!-- BARRA DE FILTROS DOS CORTES -->
      <div class="cuts-filters" aria-label="Filtrar cortes">
        <AppButton
          v-for="([id,label]) in [['all','Todos'],['generation','Em geração'],['approved','Prontos'],['exported','Exportados']]"
          :key="id"
          :class="{selected:filter===id}"
          :aria-pressed="filter===id"
          class="cuts-filter-chip"
          @click="filter=id"
        >
          {{label}}
        </AppButton>
        <AppButton type="button" class="button secondary cuts-trash" @click="$emit('deleted')">
          <Trash2 :size="14"/>Lixeira de cortes
        </AppButton>
      </div>

      <p v-if="filter!=='generation'&&revisions.length&&!visible.length" class="subtle">Nenhum corte neste estado.</p>
      <p v-if="filter==='generation'" class="subtle">Acompanhe as pendências abaixo. Prévias prontas aparecem na tabela de cortes.</p>
      <p v-if="filter==='generation'&&!jobs?.some(j=>j.operation==='render'&&j.progress?.items?.length)" class="subtle">Nenhuma prévia em geração.</p>

      <div v-if="!manual&&visible.length&&filter!=='generation'" class="review-grid">
        <!-- TABELA / LISTA DE CORTES GERADOS -->
        <section class="clip-list cuts-table-section">
          <header class="cuts-table-heading">
            <div class="table-heading-title">
              <Film :size="16"/>
              <h3>Cortes <span>{{visible.length}}</span></h3>
            </div>
            <AppButton class="button small secondary" :disabled="busy||processing||!revisions.some(r=>r.technical_pass)" @click="$emit('export')">
              <Download :size="14"/>Exportar prontos
            </AppButton>
          </header>

          <!-- AÇÕES EM LOTE (BULK ACTIONS) -->
          <div v-if="bulk.length" class="bulk-actions">
            <span class="bulk-count">{{bulk.length}} selecionado(s)</span>
            <AppButton class="button small danger" :disabled="!!deleteBlockedReason" @click="$emit('bulkDelete',[...bulk])">
              Excluir selecionados
            </AppButton>
            <AppButton class="button small secondary" :disabled="busy||processing||!exportableBulk" @click="$emit('bulkExport',[...bulk])">
              Exportar selecionados
            </AppButton>
            <AppButton class="button small secondary" @click="bulk=[]">Limpar seleção</AppButton>
            <span v-if="!exportableBulk" class="subtle">A exportação exige todos os selecionados tecnicamente válidos.</span>
          </div>

          <div class="cuts-table-scroll">
            <table class="cuts-table" aria-label="Cortes disponíveis">
              <thead>
                <tr>
                  <th scope="col" class="bulk-check">
                    <input
                      type="checkbox"
                      aria-label="Selecionar todos os cortes visíveis"
                      :checked="allVisible"
                      :indeterminate="!allVisible&&visible.some(r=>bulk.includes(r.revision_id))"
                      @change="toggleAll"
                    />
                  </th>
                  <th scope="col">Corte</th>
                  <th scope="col">Duração</th>
                  <th scope="col">Original</th>
                  <th scope="col">Estado</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(r,index) in visible"
                  :key="r.revision_id"
                  class="clip-item"
                  :class="{selected:current?.revision_id===r.revision_id}"
                  :aria-selected="current?.revision_id===r.revision_id"
                  tabindex="0"
                  @click="choose(r.revision_id)"
                  @keydown.enter.prevent="choose(r.revision_id)"
                  @keydown.space.prevent="choose(r.revision_id)"
                >
                  <td class="bulk-check" @click.stop @keydown.stop>
                    <input type="checkbox" v-model="bulk" :value="r.revision_id" :aria-label="'Selecionar corte: '+r.title"/>
                  </td>
                  <td>
                    <span class="clip-number">{{index+1}}</span>
                    <strong>{{r.title}}</strong>
                  </td>
                  <td>{{time(r.duration_us)}}</td>
                  <td>{{time(r.start_us)}} – {{time(r.end_us)}}</td>
                  <td>
                    <span class="status-pill" :data-status="r.review_status">
                      <i></i>{{labels[r.review_status]||r.review_status}}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <!-- PAINEL DE INFORMAÇÕES E ENTREGA DO CORTE SELECIONADO -->
        <section class="clip-information">
          <div class="clip-info-topbar">
            <AppButton
              type="button"
              class="button small danger delete-cut-btn"
              :disabled="!!deleteBlockedReason"
              :title="deleteBlockedReason||'Mover corte para a lixeira'"
              :aria-describedby="deleteBlockedReason?'delete-blocked-reason':undefined"
              data-action="delete-clip"
              @click="current&&$emit('delete',current.revision_id)"
            >
              <Trash2 :size="13"/>Excluir corte
            </AppButton>
            <p v-if="deleteBlockedReason" id="delete-blocked-reason" class="subtle delete-blocked-text">{{deleteBlockedReason}}</p>
          </div>

          <h2 class="preview-label">{{current?.title}}</h2>

          <div class="clip-meta-strip" v-if="current">
            <span class="meta-tag"><Clock :size="12"/>{{time(current.duration_us)}}</span>
            <span class="meta-tag">Trecho: {{time(current.start_us)}} às {{time(current.end_us)}}</span>
            <span class="status-pill" :data-status="current.review_status">
              <i></i>{{labels[current.review_status]||current.review_status}}
            </span>
          </div>

          <!-- Cópia Editorial para Redes Sociais -->
          <div class="clip-copy">
            <div class="copy-header-row">
              <h3>Descrição para publicação</h3>
              <AppButton v-if="current?.description" class="button small secondary copy-btn" title="Copiar descrição" @click="copyDescription">
                <Copy :size="13"/>Copiar
              </AppButton>
            </div>
            <div class="description-box">
              <p style="white-space:pre-line">{{current?.description||'Sem descrição gerada para este corte.'}}</p>
            </div>

            <!-- Botão de Download Principal do Arquivo MP4 9:16 -->
            <div class="download-action-box">
              <a
                v-if="current?.technical_pass&&mediaUrl&&!mediaLoading"
                class="button primary download-main-btn"
                :href="mediaUrl+(mediaUrl.includes('?')?'&':'?')+'download=1'"
                download
              >
                <Download :size="16"/>Baixar vídeo (MP4 9:16)
              </a>
              <p v-else class="subtle">Download disponível após a validação técnica.</p>
            </div>
          </div>
        </section>
      </div>

      <slot name="generation"/>
    </div>

    <!-- PLAYER VERTICAL 9:16 CALIBRADO (COLUNA DA DIREITA) -->
    <aside v-if="visible.length&&filter!=='generation'" class="cuts-player-rail" aria-label="Prévia do corte selecionado">
      <div class="clip-preview">
        <video v-if="mediaUrl" :src="mediaUrl" controls preload="metadata" playsinline></video>
        <div v-else class="video-unavailable">Prévia indisponível</div>
      </div>
      <div class="player-subcaption" v-if="current">
        <span>Formato vertical 9:16 com enquadramento inteligente e legendas ativas</span>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.cuts-review-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 24px;
  align-items: start;
}

.cuts-filters {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.cuts-filter-chip {
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 0.82rem;
  font-weight: 500;
}

.cuts-trash {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
}

.review-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.cuts-table-section {
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: var(--radius-panel, 14px);
  padding: 16px;
}

.cuts-table-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.table-heading-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-primary, var(--ink));
}

.table-heading-title h3 {
  font-size: 0.95rem;
  margin: 0;
}

.cuts-table-scroll {
  max-height: 280px;
  overflow-y: auto;
  border-radius: 8px;
}

.clip-information {
  background: var(--color-surface, var(--panel));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: var(--radius-panel, 14px);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.clip-info-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.delete-blocked-text {
  font-size: 0.77rem;
  color: var(--color-warning-text, #f59e0b);
  margin: 0;
}

.preview-label {
  font-size: 1.15rem;
  font-weight: 600;
  line-height: 1.3;
  margin: 0;
  color: var(--color-text-primary, var(--ink));
}

.clip-meta-strip {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.meta-tag {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.77rem;
  background: var(--color-surface-hover, var(--soft));
  padding: 3px 8px;
  border-radius: 6px;
  color: var(--color-text-secondary, var(--muted));
}

.clip-copy {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 6px;
}

.copy-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.copy-header-row h3 {
  font-size: 0.85rem;
  font-weight: 600;
  margin: 0;
  color: var(--color-text-primary, var(--ink));
}

.description-box {
  background: var(--color-surface-hover, var(--soft));
  border: 1px solid var(--color-border-subtle, var(--line));
  border-radius: 8px;
  padding: 12px 14px;
  font-size: 0.82rem;
  line-height: 1.5;
  color: var(--color-text-secondary, var(--muted));
  max-height: 140px;
  overflow-y: auto;
}

.download-action-box {
  margin-top: 6px;
}

.download-main-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  padding: 10px 20px;
  text-decoration: none;
}

.cuts-player-rail {
  position: sticky;
  top: 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
}

.clip-preview {
  width: 100%;
  aspect-ratio: 9/16;
  max-height: 480px;
  border-radius: 14px;
  overflow: hidden;
  background: #000;
  border: 1px solid var(--color-border-subtle, var(--line));
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
}

.clip-preview video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.player-subcaption {
  font-size: 0.72rem;
  color: var(--color-text-muted, var(--muted));
  text-align: center;
  padding: 0 8px;
}

@media (max-width: 950px) {
  .cuts-review-layout {
    grid-template-columns: 1fr;
  }
  .cuts-player-rail {
    position: static;
    max-width: 320px;
    margin: 0 auto;
  }
}
</style>
