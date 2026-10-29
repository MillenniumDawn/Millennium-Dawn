export function createOverlayFocusTrap(overlay: HTMLElement, closeButton: HTMLElement) {
  let handler: ((event: FocusEvent) => void) | null = null;

  return {
    attach(): void {
      if (handler) return;
      handler = (event: FocusEvent) => {
        if (overlay.hidden) return;
        const target = event.target as Node | null;
        if (target && overlay.contains(target)) return;
        event.preventDefault();
        event.stopPropagation();
        closeButton.focus();
      };
      document.addEventListener("focusin", handler, true);
    },

    detach(): void {
      if (!handler) return;
      document.removeEventListener("focusin", handler, true);
      handler = null;
    },
  };
}
