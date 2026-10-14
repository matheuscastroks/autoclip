import { mount, flushPromises } from '@vue/test-utils';
import { describe, it, expect } from 'vitest';
import AppSelect from '../src/components/AppSelect.vue';

const options = [
  { value: 'a', label: 'Primeiro' },
  { value: 'b', label: 'Segundo' },
  { value: 'c', label: 'Indisponível', disabled: true },
];

describe('Element Plus select component', () => {
  it('uses a custom trigger and preserves the selected exact value', async () => {
    const w = mount(AppSelect, { props: { modelValue: 'b', options, label: 'Modelo' } });
    await flushPromises();
    expect(w.find('.el-select').exists()).toBe(true);
    expect(w.find('.el-select__placeholder').text()).toContain('Segundo');
    expect(w.find('select:not([aria-hidden])').exists()).toBe(false);
    w.unmount();
  });
  it('renders options and disables the marked option', async () => {
    const w = mount(AppSelect, {
      attachTo: document.body,
      props: { modelValue: 'a', options, label: 'Modelo' },
    });
    await flushPromises();
    // trigger click on el-select wrapper to open popper
    await w.get('.el-select__wrapper').trigger('click');
    await flushPromises();
    const popper = document.querySelector('.el-select__popper');
    expect(popper).not.toBeNull();
    const disabledItem = document.querySelector('.el-select-dropdown__item.is-disabled');
    expect(disabledItem?.textContent).toContain('Indisponível');
    w.unmount();
  });
  it('does not open a disabled control', async () => {
    const w = mount(AppSelect, {
      props: { modelValue: 'a', options, label: 'Modelo', disabled: true },
    });
    await flushPromises();
    expect(w.find('.el-select__wrapper.is-disabled').exists()).toBe(true);
    expect((w.get('.el-select__input').element as HTMLInputElement).disabled).toBe(true);
    w.unmount();
  });
});
