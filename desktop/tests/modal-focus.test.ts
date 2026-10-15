import { mount } from '@vue/test-utils';
import { defineComponent, ref, h } from 'vue';
import { it, expect } from 'vitest';
import { useModalFocus } from '../src/composables/useModalFocus';

it('retains modal focus when a step transition removes the focused command', async () => {
  const Host = defineComponent({
    setup() {
      const root = ref<HTMLElement>();
      const firstStep = ref(true);
      useModalFocus(root);
      return () =>
        h(
          'div',
          { ref: root, tabindex: -1 },
          firstStep.value
            ? [
                h(
                  'button',
                  {
                    onClick: () => {
                      firstStep.value = false;
                    },
                  },
                  'Iniciar'
                ),
              ]
            : [h('p', 'Processando')]
        );
    },
  });
  const w = mount(Host, { attachTo: document.body });
  try {
    (w.get('button').element as HTMLButtonElement).focus();
    await w.get('button').trigger('click');
    expect(w.find('button').exists()).toBe(false);
    expect(document.activeElement).toBe(w.element);
  } finally {
    w.unmount();
  }
});
