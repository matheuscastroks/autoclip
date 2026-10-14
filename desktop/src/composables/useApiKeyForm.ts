import { ref } from 'vue';
import { notify } from '../notifications';
import { errorMessage } from '../utils/errors';

export interface UseApiKeyFormOptions<T = unknown> {
  saveFn: (key: string) => Promise<T>;
  successMessage?: string;
  onSuccess?: (result: T) => void;
}

export function useApiKeyForm<T = unknown>(options: UseApiKeyFormOptions<T>) {
  const { saveFn, successMessage = 'Chave armazenada com sucesso.', onSuccess } = options;

  const keyInput = ref('');
  const busy = ref(false);
  const error = ref<string | null>(null);
  const isConfigured = ref(false);

  function clear() {
    keyInput.value = '';
    error.value = null;
  }

  async function submit(): Promise<boolean> {
    const rawKey = keyInput.value.trim();
    if (!rawKey) return false;

    busy.value = true;
    error.value = null;

    try {
      const result = await saveFn(rawKey);
      keyInput.value = '';
      isConfigured.value = true;
      if (successMessage) {
        notify.success(successMessage);
      }
      onSuccess?.(result);
      return true;
    } catch (err) {
      const msg = errorMessage(err);
      error.value = msg;
      notify.error(msg);
      return false;
    } finally {
      busy.value = false;
    }
  }

  return {
    keyInput,
    busy,
    error,
    isConfigured,
    submit,
    clear,
  };
}
