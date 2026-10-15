import type { ObjectDirective } from 'vue';
import { api } from '../api';
import { notify } from '../notifications';

async function renewTicket(source: string): Promise<string> {
  const path = new URL(source, window.location.href).pathname;
  const match = path.match(/^\/api\/v1\/projects\/([^/]+)\/media\/([^/]+)$/);
  if (!match) throw new Error('Unsupported media URL');
  return api.media(decodeURIComponent(match[1]), decodeURIComponent(match[2]));
}

export function recoverMedia(
  player: HTMLVideoElement,
  renew: (source: string) => Promise<string> = renewTicket,
  failed = () =>
    notify.error('Não foi possível recuperar o vídeo. Reabra o projeto para tentar novamente.')
) {
  let generation = 0;
  let attempts = 0;
  let pending = false;
  let playing = !player.paused;
  let restore: (() => void) | undefined;
  const onPlay = () => (playing = true);
  const onPause = () => (playing = false);
  const reset = () => {
    generation++;
    attempts = 0;
    pending = false;
    if (restore) player.removeEventListener('loadedmetadata', restore);
    restore = undefined;
  };
  const onError = async () => {
    if (pending) return;
    if (restore) player.removeEventListener('loadedmetadata', restore);
    restore = undefined;
    if (attempts >= 2) {
      failed();
      return;
    }
    pending = true;
    attempts++;
    const current = generation;
    const source = player.getAttribute('src') || '';
    const position = player.currentTime;
    const resume = playing;
    const rate = player.playbackRate;
    try {
      const fresh = await renew(source);
      if (current !== generation || player.getAttribute('src') !== source) return;
      restore = () => {
        if (current !== generation) return;
        pending = false;
        restore = undefined;
        player.currentTime = Number.isFinite(position)
          ? Math.min(position, Number.isFinite(player.duration) ? player.duration : position)
          : 0;
        player.playbackRate = rate;
        if (resume) void player.play().catch(failed);
      };
      player.addEventListener('loadedmetadata', restore, { once: true });
      pending = false;
      player.src = fresh;
      player.load();
    } catch {
      if (current === generation) {
        pending = false;
        failed();
      }
    }
  };
  player.addEventListener('play', onPlay);
  player.addEventListener('pause', onPause);
  player.addEventListener('error', onError);
  return {
    reset,
    dispose() {
      reset();
      player.removeEventListener('play', onPlay);
      player.removeEventListener('pause', onPause);
      player.removeEventListener('error', onError);
    },
  };
}

const controllers = new WeakMap<HTMLVideoElement, ReturnType<typeof recoverMedia>>();
export const vRecoverMedia: ObjectDirective<HTMLVideoElement, string> = {
  mounted(player) {
    controllers.set(player, recoverMedia(player));
  },
  updated(player, binding) {
    if (binding.value !== binding.oldValue) controllers.get(player)?.reset();
  },
  unmounted(player) {
    controllers.get(player)?.dispose();
    controllers.delete(player);
  },
};
