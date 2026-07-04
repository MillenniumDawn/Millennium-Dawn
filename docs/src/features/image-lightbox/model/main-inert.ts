import { TOC_DRAWER_BODY_LOCK_CLASS } from "@/shared/config/body-scroll-lock";
import { MAIN_CONTENT_SELECTOR } from "./constants";

interface MainInertSnapshot {
  el: HTMLElement;
  wasInert: boolean;
}

export function createMainContentInert() {
  let snapshot: MainInertSnapshot | null = null;

  return {
    applyOnOpen(): void {
      const main = document.querySelector<HTMLElement>(MAIN_CONTENT_SELECTOR);
      if (!main) {
        snapshot = null;
        return;
      }
      const wasInert = main.hasAttribute("inert");
      if (!wasInert) main.setAttribute("inert", "");
      snapshot = { el: main, wasInert };
    },

    restoreAfterClose(): void {
      if (!snapshot) return;
      const { el, wasInert } = snapshot;
      snapshot = null;
      if (wasInert) return;
      if (!document.body.classList.contains(TOC_DRAWER_BODY_LOCK_CLASS)) {
        el.removeAttribute("inert");
      }
    },
  };
}
