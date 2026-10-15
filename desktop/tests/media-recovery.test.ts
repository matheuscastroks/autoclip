import { flushPromises } from '@vue/test-utils';
import { expect, it, vi } from 'vitest';
import { recoverMedia } from '../src/directives/recoverMedia';

function video() {
  const player = document.createElement('video');
  player.src = '/api/v1/projects/p/media/source?expires=1';
  player.currentTime = 42;
  player.playbackRate = 1.5;
  player.load = vi.fn();
  player.play = vi.fn().mockResolvedValue(undefined);
  return player;
}

it('renews an expired source and restores position and playback', async () => {
  const player = video();
  const renew = vi.fn().mockResolvedValue('/fresh-ticket');
  const failed = vi.fn();
  const controller = recoverMedia(player, renew, failed);
  player.dispatchEvent(new Event('play'));
  player.dispatchEvent(new Event('error'));
  await flushPromises();
  expect(renew).toHaveBeenCalledWith('/api/v1/projects/p/media/source?expires=1');
  expect(player.getAttribute('src')).toBe('/fresh-ticket');
  player.currentTime = 0;
  player.dispatchEvent(new Event('loadedmetadata'));
  expect(player.currentTime).toBe(42);
  expect(player.playbackRate).toBe(1.5);
  expect(player.play).toHaveBeenCalledOnce();
  expect(failed).not.toHaveBeenCalled();
  controller.dispose();
});

it('discards a late renewal after selecting another source', async () => {
  const player = video();
  let resolve: (url: string) => void = () => {};
  const controller = recoverMedia(player, () => new Promise(r => (resolve = r)));
  player.dispatchEvent(new Event('error'));
  player.src = '/other-source';
  controller.reset();
  resolve('/old-response');
  await flushPromises();
  expect(player.getAttribute('src')).toBe('/other-source');
  expect(player.load).not.toHaveBeenCalled();
  controller.dispose();
});

it('reports renewal failures and limits repeated retries', async () => {
  const player = video();
  const renew = vi.fn().mockRejectedValue(new Error('offline'));
  const failed = vi.fn();
  const controller = recoverMedia(player, renew, failed);
  for (let i = 0; i < 3; i++) {
    player.dispatchEvent(new Event('error'));
    await flushPromises();
  }
  expect(renew).toHaveBeenCalledTimes(2);
  expect(failed).toHaveBeenCalled();
  controller.dispose();
  player.dispatchEvent(new Event('error'));
  expect(renew).toHaveBeenCalledTimes(2);
});

it('stops when renewed URLs also fail before metadata loads', async () => {
  const player = video();
  const renew = vi.fn().mockResolvedValue('/still-unavailable');
  const failed = vi.fn();
  const controller = recoverMedia(player, renew, failed);
  for (let i = 0; i < 3; i++) {
    player.dispatchEvent(new Event('error'));
    await flushPromises();
  }
  expect(renew).toHaveBeenCalledTimes(2);
  expect(failed).toHaveBeenCalledOnce();
  controller.dispose();
});
