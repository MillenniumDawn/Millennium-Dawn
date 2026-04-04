import { splitClassList } from "@/shared/lib/dom/class-list";
import { LIGHTBOX_TRIGGER_IMAGE_CLASS } from "@/shared/ui/tailwind";
import { isEligibleLightboxImage, pickResolvedImageUrl } from "./lightbox-eligibility";
import { createBodyScrollLock } from "./body-scroll-lock";
import {
  BOUND_ATTRIBUTE,
  CLOSE_DURATION_MS,
  CONTENT_IMAGE_SELECTOR,
  MAIN_CONTENT_SELECTOR,
} from "./constants";
import { createOverlayFocusTrap } from "./focus-trap";
import { createMainContentInert } from "./main-inert";
import { mountLightboxDom } from "./mount-lightbox-dom";
import { createViewportInteractions } from "./viewport-interactions";

type Cleanup = () => void;

const NOOP: Cleanup = () => {};

const LIGHTBOX_TRIGGER_CLASSES = splitClassList(LIGHTBOX_TRIGGER_IMAGE_CLASS);

function getImageLabel(image: HTMLImageElement): string {
  const alt = image.getAttribute("alt")?.trim();
  return alt ? `Open image fullscreen: ${alt}` : "Open image fullscreen";
}

function createLightbox() {
  const refs = mountLightboxDom();
  if (!refs) return null;

  const { overlay, titleEl, viewport, image, closeButton } = refs;

  let activeTrigger: HTMLElement | null = null;
  let closeTimer = 0;

  const bodyLock = createBodyScrollLock();
  const mainInert = createMainContentInert();
  const focusTrap = createOverlayFocusTrap(overlay, closeButton);

  const clearCloseTimer = () => {
    if (closeTimer) {
      window.clearTimeout(closeTimer);
      closeTimer = 0;
    }
  };

  function close() {
    if (overlay.hidden || overlay.dataset.state === "closing") return;
    clearCloseTimer();
    overlay.dataset.state = "closing";
    closeTimer = window.setTimeout(finishClose, CLOSE_DURATION_MS);
  }

  const interactions = createViewportInteractions({
    overlay,
    viewport,
    image,
    closeButton,
    requestClose: close,
  });

  const resetOverlayToClosed = () => {
    overlay.hidden = true;
    overlay.dataset.state = "closed";
    overlay.setAttribute("aria-hidden", "true");
    image.removeAttribute("src");
    interactions.resetTransform();
    interactions.resetPointerState();
    bodyLock.unlock();
    activeTrigger?.focus({ preventScroll: true });
    activeTrigger = null;
  };

  const finishClose = () => {
    focusTrap.detach();
    mainInert.restoreAfterClose();
    resetOverlayToClosed();
  };

  const onDocumentKeyDown = (event: KeyboardEvent) => {
    if (overlay.hidden || overlay.dataset.state === "closing") return;
    if (event.key !== "Escape") return;
    event.preventDefault();
    close();
  };

  const open = (trigger: HTMLElement, src: string, alt: string) => {
    clearCloseTimer();
    activeTrigger = trigger;
    titleEl.textContent = alt.trim() ? alt : "Image";
    image.src = src;
    image.alt = alt;
    overlay.hidden = false;
    overlay.dataset.state = "closed";
    overlay.removeAttribute("aria-hidden");
    mainInert.applyOnOpen();
    focusTrap.attach();
    bodyLock.lock();
    interactions.resetTransform();

    requestAnimationFrame(() => {
      overlay.dataset.state = "open";
      closeButton.focus();
    });
  };

  interactions.bind();
  closeButton.addEventListener("click", close);
  document.addEventListener("keydown", onDocumentKeyDown, true);

  const removeChromeListeners = () => {
    closeButton.removeEventListener("click", close);
    document.removeEventListener("keydown", onDocumentKeyDown, true);
  };

  const syncTeardown = () => {
    clearCloseTimer();
    focusTrap.detach();
    mainInert.restoreAfterClose();
    if (!overlay.hidden) {
      resetOverlayToClosed();
    }
  };

  return {
    open,
    destroy: () => {
      syncTeardown();
      interactions.unbind();
      removeChromeListeners();
      overlay.remove();
    },
  };
}

export function initImageLightbox(): Cleanup {
  if (!document.querySelector(MAIN_CONTENT_SELECTOR)) return NOOP;

  const images = Array.from(document.querySelectorAll<HTMLImageElement>(CONTENT_IMAGE_SELECTOR)).filter(
    isEligibleLightboxImage,
  );
  if (!images.length) return NOOP;

  const lightbox = createLightbox();
  if (!lightbox) return NOOP;

  const cleanups: Cleanup[] = [];

  images.forEach((image) => {
    if (image.hasAttribute(BOUND_ATTRIBUTE)) return;

    image.setAttribute(BOUND_ATTRIBUTE, "true");
    image.classList.add(...LIGHTBOX_TRIGGER_CLASSES);

    if (!image.closest("a")) {
      image.tabIndex = 0;
      image.setAttribute("role", "button");
      image.setAttribute("aria-label", getImageLabel(image));
    }

    const openImage = (event?: Event) => {
      event?.preventDefault();
      const src = pickResolvedImageUrl(image);
      if (!src) return;
      lightbox.open(image, src, image.getAttribute("alt")?.trim() ?? "");
    };

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Enter" || event.key === " ") {
        openImage(event);
      }
    };

    image.addEventListener("click", openImage);
    image.addEventListener("keydown", onKeyDown);

    cleanups.push(() => {
      image.removeEventListener("click", openImage);
      image.removeEventListener("keydown", onKeyDown);
      image.classList.remove(...LIGHTBOX_TRIGGER_CLASSES);
      image.removeAttribute(BOUND_ATTRIBUTE);

      if (image.getAttribute("role") === "button") {
        image.removeAttribute("role");
        image.removeAttribute("aria-label");
        image.removeAttribute("tabindex");
      }
    });
  });

  cleanups.push(() => lightbox.destroy());

  return () => {
    while (cleanups.length) {
      const cleanup = cleanups.pop();
      cleanup?.();
    }
  };
}
