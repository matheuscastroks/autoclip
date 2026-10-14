import { ref } from 'vue';
import { notify } from '../notifications';
import { errorMessage } from '../utils/errors';

export function useAction() {
  const busy = ref(false);

  async function execute<T>(fn: () => Promise<T>, successMessage = ''): Promise<T | undefined> {
    if (busy.value) return undefined;
    busy.value = true;
    try {
      const result = await fn();
      if (successMessage) {
        notify.success(successMessage);
      }
      return result;
    } catch (error) {
      notify.error(errorMessage(error));
      return undefined;
    } finally {
      busy.value = false;
    }
  }

  return {
    busy,
    execute,
  };
}
