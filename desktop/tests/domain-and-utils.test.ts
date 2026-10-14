import { describe, it, expect } from 'vitest';
import { isFailed, isRunning, isActive, statusTagType } from '../src/domain/jobStatus';
import { overlaps, overlapsAny } from '../src/utils/intervals';
import { errorMessage } from '../src/utils/errors';
import { time } from '../src/format';

describe('domain/jobStatus', () => {
  it('identifica status com falha', () => {
    expect(isFailed('failed')).toBe(true);
    expect(isFailed('cancelled')).toBe(true);
    expect(isFailed('interrupted')).toBe(true);
    expect(isFailed('completed')).toBe(false);
    expect(isFailed('running')).toBe(false);
  });

  it('identifica status em execução', () => {
    expect(isRunning('running')).toBe(true);
    expect(isRunning('processing')).toBe(true);
    expect(isRunning('cancelling')).toBe(true);
    expect(isRunning('pending')).toBe(false);
  });

  it('identifica status ativos', () => {
    expect(isActive('pending')).toBe(true);
    expect(isActive('running')).toBe(true);
    expect(isActive('completed')).toBe(false);
  });

  it('retorna tipo correto de tag para o status', () => {
    expect(statusTagType('completed')).toBe('success');
    expect(statusTagType('ready')).toBe('success');
    expect(statusTagType('running')).toBe('primary');
    expect(statusTagType('failed')).toBe('danger');
    expect(statusTagType('needs_review')).toBe('warning');
    expect(statusTagType('pending')).toBe('info');
    expect(statusTagType('unknown_status')).toBe('info');
  });
});

describe('utils/intervals', () => {
  it('detecta sobreposição entre dois intervalos', () => {
    expect(overlaps({ start: 10, end: 30 }, { start: 20, end: 40 })).toBe(true);
    expect(overlaps({ start: 10, end: 20 }, { start: 20, end: 30 })).toBe(false);
    expect(overlaps({ start: 10, end: 20 }, { start: 25, end: 30 })).toBe(false);
    expect(overlaps({ start: 0, end: 100 }, { start: 20, end: 50 })).toBe(true);
  });

  it('detecta sobreposição em lista com overlapsAny', () => {
    const list = [
      { start: 0, end: 10 },
      { start: 50, end: 80 },
    ];
    expect(overlapsAny({ start: 5, end: 15 }, list)).toBe(true);
    expect(overlapsAny({ start: 15, end: 45 }, list)).toBe(false);
    expect(overlapsAny({ start: 70, end: 90 }, list)).toBe(true);
  });
});

describe('utils/errors', () => {
  it('extrai mensagem de erro de forma resiliente', () => {
    expect(errorMessage(new Error('Falha de conexão'))).toBe('Falha de conexão');
    expect(errorMessage('Erro como string')).toBe('Erro como string');
    expect(errorMessage({ message: 'Objeto de erro' })).toBe('Objeto de erro');
    expect(errorMessage(null, 'Fallback padrão')).toBe('Fallback padrão');
    expect(errorMessage(undefined)).toBe('Ocorreu um erro inesperado.');
  });
});

describe('format/time', () => {
  it('formata segundos e minutos corretamente', () => {
    expect(time(0)).toBe('00:00');
    expect(time(65 * 1e6)).toBe('01:05');
    expect(time(59 * 60 * 1e6)).toBe('59:00');
  });

  it('formata horas quando ultrapassa 59 minutos', () => {
    expect(time(75 * 60 * 1e6)).toBe('01:15:00');
    expect(time(3600 * 1e6)).toBe('01:00:00');
    expect(time((2 * 3600 + 30 * 60 + 15) * 1e6)).toBe('02:30:15');
  });
});
