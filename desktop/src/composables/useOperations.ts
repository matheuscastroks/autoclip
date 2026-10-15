import { computed, ref } from 'vue';
import { notify } from '../notifications';

export function useOperations() {
  const pending = ref(new Set<string>());
  const isPending = (key: string) => pending.value.has(key);
  async function run<T>(key: string, task: () => Promise<T>, success = '') {
    if (isPending(key)) return;
    pending.value = new Set([...pending.value, key]);
    try {
      const result = await task();
      if (success) notify.success(success);
      return result;
    } catch (error) {
      notify.error(
        error instanceof Error ? error.message : 'Não foi possível concluir esta operação.'
      );
    } finally {
      const remaining = new Set(pending.value);
      remaining.delete(key);
      pending.value = remaining;
    }
  }
  return { run, pending, isPending, anyPending: computed(() => pending.value.size > 0) };
}
