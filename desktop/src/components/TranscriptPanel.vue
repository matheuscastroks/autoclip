<script setup lang="ts">
import { computed, ref, onBeforeUnmount, watch } from 'vue';
import type { Transcript } from '../types';
import { time } from '../format';
import { vRecoverMedia } from '../directives/recoverMedia';
import AppIcon from './ui/AppIcon.vue';
const props = defineProps<{
  transcript: Transcript | null;
  sourceUrl: string;
  wordCount: number;
}>();
const query = defineModel<string>('query', { default: '' });
const player = ref<HTMLVideoElement>();
const positionUs = ref(0);
const mediaError = ref('');
const segments = computed(() =>
  props.transcript?.segments.length
    ? props.transcript.segments
    : props.transcript?.words.reduce<Transcript['segments']>((all, word, index) => {
        if (index % 12 === 0)
          all.push({ id: word.id, text: word.text, start_us: word.start_us, end_us: word.end_us });
        else {
          all[all.length - 1].text += ' ' + word.text;
          all[all.length - 1].end_us = word.end_us;
        }
        return all;
      }, []) || []
);
const filtered = computed(() =>
  segments.value.filter(s =>
    s.text.toLocaleLowerCase('pt-BR').includes(query.value.trim().toLocaleLowerCase('pt-BR'))
  )
);
async function seek(us: number) {
  if (!player.value) return;
  player.value.currentTime = us / 1e6;
  positionUs.value = us;
  mediaError.value = '';
  try {
    await player.value.play();
  } catch {
    mediaError.value =
      'Não foi possível iniciar a reprodução. Use os controles do vídeo para tentar novamente.';
  }
}
function release() {
  if (!player.value) return;
  player.value.pause();
  player.value.removeAttribute('src');
  player.value.load();
}
watch(
  () => props.transcript,
  value => {
    if (!value) release();
  },
  { flush: 'sync' }
);
onBeforeUnmount(release);
</script>
<template>
  <section class="transcript-panel" aria-label="Consulta da transcrição">
    <header class="transcript-panel-header">
      <div>
        <h2>Transcrição original</h2>
        <p>
          {{ wordCount.toLocaleString('pt-BR') }} palavras · Consulta opcional para conferir o
          contexto
        </p>
      </div>
      <label class="transcript-query"
        ><AppIcon name="search" size="sm" /><input
          v-model="query"
          type="search"
          placeholder="Buscar termos na fala..."
          aria-label="Buscar na transcrição"
      /></label>
    </header>
    <div v-if="transcript" class="transcript-panel-regions">
      <section class="transcript-original" aria-label="Vídeo original">
        <video
          v-if="sourceUrl"
          ref="player"
          v-recover-media="sourceUrl"
          :src="sourceUrl"
          controls
          preload="metadata"
          playsinline
          aria-label="Original transcrito"
          @timeupdate="positionUs = (player?.currentTime || 0) * 1e6"
          @loadedmetadata="mediaError = ''"
        />
        <p v-else>Vídeo indisponível. A transcrição permanece disponível para consulta.</p>
        <p v-if="mediaError" role="alert">{{ mediaError }}</p>
        <small
          >Use os timestamps para reproduzir o trecho. O texto pode ser selecionado e
          copiado.</small
        >
      </section>
      <section class="transcript-passages" tabindex="0" aria-label="Segmentos da transcrição">
        <article
          v-for="segment in filtered"
          :key="segment.id"
          class="transcript-segment-row"
          :class="{ current: positionUs >= segment.start_us && positionUs < segment.end_us }"
          :aria-current="
            positionUs >= segment.start_us && positionUs < segment.end_us ? 'true' : undefined
          "
        >
          <button
            type="button"
            :data-segment="segment.id"
            :disabled="!sourceUrl"
            :aria-label="'Reproduzir a partir de ' + time(segment.start_us)"
            @click="seek(segment.start_us)"
          >
            <time>{{ time(segment.start_us) }}</time>
          </button>
          <p>{{ segment.text }}</p>
        </article>
        <p v-if="!filtered.length" class="transcript-empty">
          {{
            query
              ? 'Nenhum trecho corresponde à busca. Ajuste o termo para continuar.'
              : 'A transcrição não contém trechos disponíveis.'
          }}
        </p>
      </section>
    </div>
    <section v-else class="transcript-empty">
      <h3>Ainda sem transcrição</h3>
      <p>
        Inicie ou recupere a transcrição na aba Preparação. Não é necessário aprovar esta consulta
        para gerar cortes.
      </p>
    </section>
  </section>
</template>
<style scoped>
.transcript-panel {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-height: 0;
  min-width: 0;
  height: 100%;
}
.transcript-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
h2 {
  font-size: var(--font-size-region);
}
.transcript-panel-header p,
small {
  color: var(--color-text-secondary);
  font-size: var(--font-size-meta);
}
.transcript-query {
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 6px 10px;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border-subtle);
  border-radius: var(--radius-control);
}
.transcript-query:focus-within {
  outline: 2px solid var(--color-focus-ring);
  outline-offset: 2px;
}
.transcript-query input {
  min-width: 0;
  background: transparent;
  color: var(--color-text-primary);
  border: 0;
}
.transcript-panel-regions {
  display: grid;
  grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.2fr);
  gap: 24px;
  min-height: 0;
  flex: 1;
}
.transcript-original {
  min-width: 0;
  overflow: auto;
}
.transcript-original video {
  display: block;
  width: 100%;
  aspect-ratio: 16/9;
  background: var(--color-canvas);
  max-height: 420px;
}
.transcript-original small {
  display: block;
  margin-top: 12px;
}
.transcript-passages {
  overflow: auto;
  min-width: 0;
  min-height: 0;
}
.transcript-segment-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 16px;
  padding: 12px;
  border: 0;
  border-bottom: 1px solid var(--color-border-subtle);
  background: transparent;
  border-radius: 0;
}
.transcript-segment-row.current {
  background: var(--color-surface-selected);
}
.transcript-segment-row button {
  background: transparent;
  border: 0;
  padding: 0;
  align-self: start;
  color: var(--color-action-primary);
  font-size: var(--font-size-meta);
}
.transcript-segment-row p {
  user-select: text;
  margin: 0;
  font-size: var(--font-size-body);
  overflow-wrap: anywhere;
}
.transcript-empty {
  padding: 24px 0;
  color: var(--color-text-secondary);
}
.transcript-empty h3 {
  color: var(--color-text-primary);
  font-size: var(--font-size-region);
  margin-bottom: 8px;
}
@media (max-width: 1050px) {
  .transcript-panel {
    gap: 16px;
  }
  .transcript-panel-regions {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: auto minmax(0, 1fr);
    gap: 16px;
  }
  .transcript-original video {
    max-height: 190px;
  }
  .transcript-original small {
    margin-top: 4px;
  }
}
</style>
