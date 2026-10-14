import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ApiError, setSessionToken, getSessionToken, request, post, put, del } from '../src/api/client';
import { usePolling } from '../src/composables/usePolling';

describe('api/client', () => {
  beforeEach(() => {
    setSessionToken('');
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('instancia ApiError com propriedades tipadas', () => {
    const error = new ApiError('Não encontrado', { status: 404, code: 'NOT_FOUND' });
    expect(error.name).toBe('ApiError');
    expect(error.status).toBe(404);
    expect(error.code).toBe('NOT_FOUND');
    expect(error.isNotFound).toBe(true);
    expect(error.isNetworkError).toBe(false);
    expect(error.isUnauthorized).toBe(false);
  });

  it('detecta erros de rede com status 0', () => {
    const netErr = new ApiError('Sem conexão', { status: 0 });
    expect(netErr.isNetworkError).toBe(true);
  });

  it('armazena e recupera o token de sessão', () => {
    setSessionToken('jwt-token-123');
    expect(getSessionToken()).toBe('jwt-token-123');
  });

  it('faz requisição com sucesso retornando JSON tipado', async () => {
    const mockResponse = { id: 'p1', name: 'Projeto Teste' };
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      headers: { get: () => 'application/json' },
      json: async () => mockResponse,
    }));

    const result = await request<typeof mockResponse>('/projects/p1');
    expect(result).toEqual(mockResponse);
  });

  it('lança ApiError com mensagem do backend quando status !ok', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      headers: { get: () => 'application/json' },
      json: async () => ({ detail: 'Parâmetro inválido' }),
    }));

    await expect(request('/bad-request')).rejects.toThrow('Parâmetro inválido');
  });
});

describe('composables/usePolling', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('inicia e executa callback de polling', async () => {
    const callback = vi.fn().mockResolvedValue(true);
    const { start, stop, isPolling } = usePolling(callback, {
      intervalMs: 1000,
      immediate: true,
      pauseWhenHidden: false,
    });

    start();
    expect(isPolling.value).toBe(true);
    expect(callback).toHaveBeenCalledTimes(1);

    await vi.advanceTimersByTimeAsync(1000);
    expect(callback).toHaveBeenCalledTimes(2);

    stop();
    expect(isPolling.value).toBe(false);

    await vi.advanceTimersByTimeAsync(2000);
    expect(callback).toHaveBeenCalledTimes(2);
  });
});
