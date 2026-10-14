import { ref, onMounted, onUnmounted, getCurrentInstance } from 'vue';

export interface UsePollingOptions {
  intervalMs?: number;
  pauseWhenHidden?: boolean;
  maxConsecutiveErrors?: number;
  backoffMultiplier?: number;
  maxIntervalMs?: number;
  immediate?: boolean;
}

export function usePolling(
  callback: () => Promise<unknown>,
  options: UsePollingOptions = {}
) {
  const {
    intervalMs = 3000,
    pauseWhenHidden = true,
    maxConsecutiveErrors = 5,
    backoffMultiplier = 1.5,
    maxIntervalMs = 30000,
    immediate = true,
  } = options;

  let timerId: ReturnType<typeof setTimeout> | null = null;
  let running = false;
  let consecutiveErrors = 0;
  let currentInterval = intervalMs;

  const isPolling = ref(false);
  const isExecuting = ref(false);
  const lastError = ref<unknown>(null);

  async function executeTick() {
    if (!running) return;

    if (pauseWhenHidden && typeof document !== 'undefined' && document.hidden) {
      scheduleNext(intervalMs);
      return;
    }

    isExecuting.value = true;
    try {
      await callback();
      consecutiveErrors = 0;
      currentInterval = intervalMs;
      lastError.value = null;
    } catch (err) {
      consecutiveErrors++;
      lastError.value = err;
      if (consecutiveErrors >= maxConsecutiveErrors) {
        currentInterval = Math.min(currentInterval * backoffMultiplier, maxIntervalMs);
      }
    } finally {
      isExecuting.value = false;
      if (running) {
        scheduleNext(currentInterval);
      }
    }
  }

  function scheduleNext(delay: number) {
    clear();
    timerId = setTimeout(executeTick, delay);
  }

  function clear() {
    if (timerId !== null) {
      clearTimeout(timerId);
      timerId = null;
    }
  }

  function start() {
    if (running) return;
    running = true;
    isPolling.value = true;
    consecutiveErrors = 0;
    currentInterval = intervalMs;

    if (immediate) {
      void executeTick();
    } else {
      scheduleNext(currentInterval);
    }
  }

  function stop() {
    running = false;
    isPolling.value = false;
    clear();
  }

  function handleVisibilityChange() {
    if (!running) return;
    if (typeof document !== 'undefined' && !document.hidden) {
      // Retomou visibilidade: executa imediatamente
      clear();
      void executeTick();
    }
  }

  if (typeof window !== 'undefined' && getCurrentInstance()) {
    onMounted(() => {
      if (pauseWhenHidden && typeof document !== 'undefined') {
        document.addEventListener('visibilitychange', handleVisibilityChange);
      }
    });

    onUnmounted(() => {
      stop();
      if (pauseWhenHidden && typeof document !== 'undefined') {
        document.removeEventListener('visibilitychange', handleVisibilityChange);
      }
    });
  }

  return {
    isPolling,
    isExecuting,
    lastError,
    start,
    stop,
    triggerNow: () => {
      clear();
      return executeTick();
    },
  };
}
