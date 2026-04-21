import { splitClassList } from "@/shared/lib/dom/class-list";
import { LIGHTBOX_LOCK_BODY_CLASS } from "@/shared/ui/tailwind";
import { SCROLL_TOP_CSS_VAR, SCROLLBAR_COMPENSATION_CSS_VAR } from "./constants";

const LOCK_BODY_CLASSES = splitClassList(LIGHTBOX_LOCK_BODY_CLASS);

export function createBodyScrollLock() {
  let lockedScrollY = 0;
  let active = false;

  return {
    lock(): void {
      active = true;
      lockedScrollY = window.scrollY;
      const scrollbarCompensation = Math.max(0, window.innerWidth - document.documentElement.clientWidth);
      document.body.style.setProperty(SCROLL_TOP_CSS_VAR, `-${lockedScrollY}px`);
      document.body.style.setProperty(SCROLLBAR_COMPENSATION_CSS_VAR, `${scrollbarCompensation}px`);
      document.body.classList.add(...LOCK_BODY_CLASSES);
    },

    unlock(): void {
      if (!active) return;
      active = false;
      document.body.classList.remove(...LOCK_BODY_CLASSES);
      document.body.style.removeProperty(SCROLL_TOP_CSS_VAR);
      document.body.style.removeProperty(SCROLLBAR_COMPENSATION_CSS_VAR);
      window.scrollTo({ top: lockedScrollY, left: 0, behavior: "instant" as ScrollBehavior });
    },
  };
}
