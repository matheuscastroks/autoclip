import { onMounted, onBeforeUnmount, onUpdated, type Ref } from 'vue';

// For existing custom overlays; native dialogs and Element Plus Drawers own their focus.
export function useModalFocus(root: Ref<HTMLElement | undefined>) {
  let opener: HTMLElement | null = null;
  function trap(event: KeyboardEvent) {
    const modal = root.value;
    if (event.key !== 'Tab' || !modal) return;
    const controls = Array.from(
      modal.querySelectorAll<HTMLElement>(
        'button:not(:disabled), a[href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex="0"]'
      )
    ).filter(el => {
      for (let node: HTMLElement | null = el; node && node !== modal; node = node.parentElement) {
        if (
          node.hidden ||
          getComputedStyle(node).display === 'none' ||
          getComputedStyle(node).visibility === 'hidden'
        )
          return false;
      }
      return true;
    });
    const first = controls[0],
      last = controls.at(-1);
    if (!first) {
      event.preventDefault();
      modal.focus();
      return;
    }
    if (event.shiftKey && (document.activeElement === first || document.activeElement === modal)) {
      event.preventDefault();
      last?.focus();
    } else if (
      !event.shiftKey &&
      (document.activeElement === last || document.activeElement === modal)
    ) {
      event.preventDefault();
      first.focus();
    }
  }
  onMounted(() => {
    opener = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    root.value?.addEventListener('keydown', trap);
    root.value?.focus();
  });
  onUpdated(() => {
    // A focused step command can be removed by a successful async transition.
    if (document.activeElement === document.body) root.value?.focus();
  });
  onBeforeUnmount(() => {
    root.value?.removeEventListener('keydown', trap);
    if (opener?.isConnected) opener.focus();
  });
}
