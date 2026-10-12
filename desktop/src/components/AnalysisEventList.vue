<script setup lang="ts">
import {computed} from 'vue'
import type {AnalysisEvent} from '../types'
import {time} from '../format'
const props=defineProps<{events:AnalysisEvent[]}>()
const blocks=computed(()=>{
  const rows:AnalysisEvent[]=[]
  for(const event of props.events){
    const previous=rows.at(-1)
    if(event.kind==='thought_summary'&&previous?.kind==='thought_summary'&&event.attempt===previous.attempt&&event.window_id===previous.window_id)previous.message+=event.message
    else rows.push({...event})
  }
  return rows
})
</script>
<template>
  <article v-for="event in blocks" :key="event.id" class="analysis-event" :data-event-kind="event.kind">
    <div class="event-heading"><strong>{{event.kind==='thought_summary'?'Resumo enviado pelo Gemini':'Evento do aplicativo'}}</strong><small>{{event.at?new Date(event.at).toLocaleTimeString('pt-BR'):''}}<template v-if="event.window_index"> · janela {{event.window_index}}</template><template v-if="event.attempt"> · tentativa {{event.attempt}}</template></small></div>
    <p :class="{'thought-text':event.kind==='thought_summary'}">{{event.message}}</p>
    <div v-for="topic in event.topics" :key="topic.id" class="analysis-topic"><strong>{{topic.label}}</strong><p>{{topic.summary}}</p></div>
    <div v-for="candidate in event.candidates" :key="candidate.id" class="analysis-candidate"><strong>{{candidate.title_suggestion||'Proposta de corte'}}</strong><small v-if="candidate.start_us!==undefined">{{time(candidate.start_us)}} – {{time(candidate.end_us)}}</small><p>{{candidate.rationale}}</p><small>Palavras {{candidate.start_word_id}} → {{candidate.end_word_id}} · proposta sem aprovação editorial</small></div>
    <small v-if="event.usage">Tokens de pensamento: {{event.usage.thoughts_token_count??'não informado'}} · saída: {{event.usage.candidates_token_count??'não informado'}}</small>
  </article>
</template>
