export interface ApiErrorOptions {
  status?: number;
  code?: string;
  cause?: unknown;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;

  constructor(message: string, options: ApiErrorOptions = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = options.status ?? 0;
    this.code = options.code;
    if (options.cause) {
      this.cause = options.cause;
    }
  }

  get isNetworkError(): boolean {
    return this.status === 0;
  }

  get isNotFound(): boolean {
    return this.status === 404;
  }

  get isUnauthorized(): boolean {
    return this.status === 401 || this.status === 403;
  }
}

let sessionToken = '';

export function setSessionToken(token: string) {
  sessionToken = token;
}

export function getSessionToken(): string {
  return sessionToken;
}

export function initializeSession() {
  if (typeof window === 'undefined') return;
  const hash = window.location.hash.slice(1);
  const token = new URLSearchParams(hash).get('session') || '';
  setSessionToken(token);
  if (window.location.hash) {
    window.history.replaceState(null, '', window.location.pathname + window.location.search);
  }
}

export interface RequestOptions extends RequestInit {
  timeoutMs?: number;
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { timeoutMs = 30000, ...fetchOptions } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  if (fetchOptions.signal) {
    fetchOptions.signal.addEventListener('abort', () => controller.abort());
  }

  try {
    const response = await fetch('/api/v1' + path, {
      ...fetchOptions,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        Authorization: sessionToken ? 'Bearer ' + sessionToken : '',
        ...fetchOptions.headers,
      },
    });

    const isJson = response.headers.get('content-type')?.includes('application/json');
    let data: unknown;
    try {
      data = isJson ? await response.json() : await response.text();
    } catch {
      data = null;
    }

    if (!response.ok) {
      const errorData = data as { detail?: string | { code?: string; message?: string } } | null;
      const detail = errorData?.detail;

      let message = 'Não foi possível concluir a operação.';
      let code: string | undefined;

      if (typeof detail === 'string') {
        message = detail;
      } else if (detail && typeof detail === 'object') {
        code = detail.code;
        message = detail.message || (code ? `Erro ${code}` : message);
      } else if (response.statusText) {
        message = response.statusText;
      }

      throw new ApiError(message, {
        status: response.status,
        code,
      });
    }

    return data as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError('A requisição excedeu o tempo limite.', { status: 408, code: 'TIMEOUT' });
    }
    const message = error instanceof Error ? error.message : 'Falha de comunicação com o servidor local.';
    throw new ApiError(message, { status: 0, cause: error });
  } finally {
    clearTimeout(timeoutId);
  }
}

export const post = <T>(path: string, body?: unknown, options: RequestOptions = {}) =>
  request<T>(path, {
    method: 'POST',
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    ...options,
  });

export const put = <T>(path: string, body?: unknown, options: RequestOptions = {}) =>
  request<T>(path, {
    method: 'PUT',
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    ...options,
  });

export const del = <T>(path: string, options: RequestOptions = {}) =>
  request<T>(path, {
    method: 'DELETE',
    ...options,
  });
