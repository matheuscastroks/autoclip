import { expect, it, vi } from 'vitest';
import { useOperations } from '../src/composables/useOperations';
import { notify } from '../src/notifications';

it('allows unrelated operations while rejecting a duplicate operation', async () => {
  const operations = useOperations();
  let finish: () => void = () => {};
  const saving = operations.run('settings', () => new Promise<void>(resolve => (finish = resolve)));
  const duplicate = vi.fn();
  await operations.run('settings', duplicate);
  const cancel = vi.fn().mockResolvedValue(undefined);
  await operations.run('job:one', cancel);
  expect(cancel).toHaveBeenCalledOnce();
  expect(duplicate).not.toHaveBeenCalled();
  expect(operations.isPending('settings')).toBe(true);
  expect(operations.isPending('job:one')).toBe(false);
  finish();
  await saving;
  expect(operations.anyPending.value).toBe(false);
});

it('reports a failed operation and permits retry', async () => {
  const report = vi.spyOn(notify, 'error');
  const operations = useOperations();
  await operations.run('save', async () => {
    throw new Error('fixture failure');
  });
  expect(report).toHaveBeenCalledWith('fixture failure');
  const retry = vi.fn().mockResolvedValue('saved');
  expect(await operations.run('save', retry)).toBe('saved');
  expect(operations.anyPending.value).toBe(false);
  report.mockRestore();
});
