import { isEligibleLightboxImage, pickResolvedImageUrl } from "@/features/image-lightbox/lib/eligibility";
import { TOC_DRAWER_BODY_LOCK_CLASS } from "@/shared/config/body-scroll-lock";
import {
  LIGHTBOX_CLOSE_BUTTON_CLASS,
  LIGHTBOX_CONTENT_CLASS,
  LIGHTBOX_IMAGE_CLASS,
  LIGHTBOX_LOCK_BODY_CLASS,
  LIGHTBOX_OVERLAY_CLASS,
  LIGHTBOX_TRIGGER_IMAGE_CLASS,
  LIGHTBOX_VIEWPORT_CLASS,
} from "@/shared/ui/tailwind";

type Cleanup = () => void;

interface Point {
  x: number;
  y: number;
}

interface MainInertSnapshot {
  el: HTMLElement;
  wasInert: boolean;
}

const NOOP: Cleanup = () => {};
const MAIN_CONTENT_SELECTOR = "#main-content";
/** Scope lightbox to main content only (avoids header/footer chrome and duplicate work on large DOMs). */
const CONTENT_IMAGE_SELECTOR = `${MAIN_CONTENT_SELECTOR} img`;
const BOUND_ATTRIBUTE = "data-image-lightbox-bound";
const LIGHTBOX_TITLE_ID = "image-lightbox-title";
const MIN_SCALE = 1;
const MAX_SCALE = 5;
const WHEEL_STEP = 0.2;
const CLOSE_DURATION_MS = 180;
const SCROLL_TOP_CSS_VAR = "--lightbox-scroll-top";
const SCROLLBAR_COMPENSATION_CSS_VAR = "--lightbox-scrollbar-compensation";

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function getImageLabel(image: HTMLImageElement): string {
  const alt = image.getAttribute("alt")?.trim();
  return alt ? `Open image fullscreen: ${alt}` : "Open image fullscreen";
}

function getDistance(first: Point, second: Point): number {
  return Math.hypot(second.x - first.x, second.y - first.y);
}

function getMidpoint(first: Point, second: Point): Point {
  return {
    x: (first.x + second.x) / 2,
    y: (first.y + second.y) / 2,
  };
}

function getBaseImageSize(image: HTMLImageElement, viewport: HTMLElement): { width: number; height: number } {
  const naturalWidth = image.naturalWidth || viewport.clientWidth || 1;
  const naturalHeight = image.naturalHeight || viewport.clientHeight || 1;
  const viewportWidth = viewport.clientWidth || naturalWidth;
  const viewportHeight = viewport.clientHeight || naturalHeight;
  const fitRatio = Math.min(viewportWidth / naturalWidth, viewportHeight / naturalHeight, 1);

  return {
    width: naturalWidth * fitRatio,
    height: naturalHeight * fitRatio,
  };
}

function createLightbox() {
  const overlay = document.createElement("div");
  overlay.className = LIGHTBOX_OVERLAY_CLASS;
  overlay.setAttribute("data-image-lightbox-overlay", "");
  overlay.setAttribute("role", "dialog");
  overlay.setAttribute("aria-modal", "true");
  overlay.setAttribute("aria-labelledby", LIGHTBOX_TITLE_ID);
  overlay.hidden = true;
  overlay.dataset.state = "closed";
  overlay.dataset.zoomed = "false";
  overlay.setAttribute("aria-hidden", "true");
  overlay.innerHTML = `
    <h2 class="sr-only" id="${LIGHTBOX_TITLE_ID}"></h2>
    <button class="${LIGHTBOX_CLOSE_BUTTON_CLASS}" type="button" aria-label="Close image viewer" data-image-lightbox-close>
      <svg class="size-6 shrink-0" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
        <path d="M18.3 5.71a1 1 0 0 0-1.41 0L12 10.59 7.11 5.7A1 1 0 0 0 5.7 7.11L10.59 12 5.7 16.89a1 1 0 1 0 1.41 1.41L12 13.41l4.89 4.89a1 1 0 0 0 1.41-1.41L13.41 12l4.89-4.89a1 1 0 0 0 0-1.4z"></path>
      </svg>
    </button>
    <div class="${LIGHTBOX_VIEWPORT_CLASS}" data-image-lightbox-viewport>
      <div class="${LIGHTBOX_CONTENT_CLASS}" data-image-lightbox-content>
        <img class="${LIGHTBOX_IMAGE_CLASS}" alt="" draggable="false" data-image-lightbox-image />
      </div>
    </div>
  `;

  document.body.append(overlay);

  const titleEl = overlay.querySelector<HTMLHeadingElement>(`#${LIGHTBOX_TITLE_ID}`);
  const viewport = overlay.querySelector<HTMLElement>("[data-image-lightbox-viewport]");
  const image = overlay.querySelector<HTMLImageElement>("[data-image-lightbox-image]");
  const closeButton = overlay.querySelector<HTMLButtonElement>("[data-image-lightbox-close]");

  if (!titleEl || !viewport || !image || !closeButton) {
    overlay.remove();
    return null;
  }

  let scale = MIN_SCALE;
  let offsetX = 0;
  let offsetY = 0;
  let activeTrigger: HTMLElement | null = null;
  let closeTimer = 0;
  let lockedScrollY = 0;
  let bodyScrollLocked = false;
  let dragPointerId: number | null = null;
  let dragLastPoint: Point | null = null;
  let pinchStartDistance = 0;
  let pinchStartScale = MIN_SCALE;
  let pinchStartOffset = { x: 0, y: 0 };
  let pinchStartMidpoint: Point | null = null;
  const pointers = new Map<number, Point>();

  let mainInertSnapshot: MainInertSnapshot | null = null;
  let focusTrapHandler: ((event: FocusEvent) => void) | null = null;

  const clearCloseTimer = () => {
    if (closeTimer) {
      window.clearTimeout(closeTimer);
      closeTimer = 0;
    }
  };

  const applyMainInertOnOpen = () => {
    const main = document.querySelector<HTMLElement>(MAIN_CONTENT_SELECTOR);
    if (!main) {
      mainInertSnapshot = null;
      return;
    }
    const wasInert = main.hasAttribute("inert");
    if (!wasInert) main.setAttribute("inert", "");
    mainInertSnapshot = { el: main, wasInert };
  };

  const restoreMainInertAfterClose = () => {
    if (!mainInertSnapshot) return;
    const { el, wasInert } = mainInertSnapshot;
    mainInertSnapshot = null;
    if (wasInert) return;
    if (!document.body.classList.contains(TOC_DRAWER_BODY_LOCK_CLASS)) {
      el.removeAttribute("inert");
    }
  };

  const attachFocusTrap = () => {
    if (focusTrapHandler) return;
    focusTrapHandler = (event: FocusEvent) => {
      if (overlay.hidden) return;
      const target = event.target as Node | null;
      if (target && overlay.contains(target)) return;
      event.preventDefault();
      event.stopPropagation();
      closeButton.focus();
    };
    document.addEventListener("focusin", focusTrapHandler, true);
  };

  const detachFocusTrap = () => {
    if (!focusTrapHandler) return;
    document.removeEventListener("focusin", focusTrapHandler, true);
    focusTrapHandler = null;
  };

  const clampOffsets = (nextScale: number, nextOffsetX: number, nextOffsetY: number) => {
    const baseSize = getBaseImageSize(image, viewport);
    const scaledWidth = baseSize.width * nextScale;
    const scaledHeight = baseSize.height * nextScale;
    const maxOffsetX = Math.max(0, (scaledWidth - viewport.clientWidth) / 2);
    const maxOffsetY = Math.max(0, (scaledHeight - viewport.clientHeight) / 2);

    return {
      x: clamp(nextOffsetX, -maxOffsetX, maxOffsetX),
      y: clamp(nextOffsetY, -maxOffsetY, maxOffsetY),
    };
  };

  const render = () => {
    const clamped = clampOffsets(scale, offsetX, offsetY);
    offsetX = clamped.x;
    offsetY = clamped.y;
    image.style.transform = `translate3d(${offsetX}px, ${offsetY}px, 0) scale(${scale})`;
    overlay.dataset.zoomed = scale > MIN_SCALE ? "true" : "false";
  };

  const setTransform = (nextScale: number, nextOffsetX = offsetX, nextOffsetY = offsetY) => {
    scale = clamp(Number(nextScale.toFixed(3)), MIN_SCALE, MAX_SCALE);
    const clamped = clampOffsets(scale, nextOffsetX, nextOffsetY);
    offsetX = clamped.x;
    offsetY = clamped.y;
    render();
  };

  const resetTransform = () => {
    scale = MIN_SCALE;
    offsetX = 0;
    offsetY = 0;
    render();
  };

  const lockBody = () => {
    bodyScrollLocked = true;
    lockedScrollY = window.scrollY;
    const scrollbarCompensation = Math.max(0, window.innerWidth - document.documentElement.clientWidth);
    document.body.style.setProperty(SCROLL_TOP_CSS_VAR, `-${lockedScrollY}px`);
    document.body.style.setProperty(SCROLLBAR_COMPENSATION_CSS_VAR, `${scrollbarCompensation}px`);
    document.body.classList.add(...LIGHTBOX_LOCK_BODY_CLASS.split(" "));
  };

  const unlockBody = () => {
    if (!bodyScrollLocked) return;
    bodyScrollLocked = false;
    document.body.classList.remove(...LIGHTBOX_LOCK_BODY_CLASS.split(" "));
    document.body.style.removeProperty(SCROLL_TOP_CSS_VAR);
    document.body.style.removeProperty(SCROLLBAR_COMPENSATION_CSS_VAR);
    window.scrollTo({ top: lockedScrollY, left: 0, behavior: "instant" as ScrollBehavior });
  };

  const finishClose = () => {
    detachFocusTrap();
    restoreMainInertAfterClose();
    overlay.hidden = true;
    overlay.dataset.state = "closed";
    overlay.setAttribute("aria-hidden", "true");
    image.removeAttribute("src");
    resetTransform();
    pointers.clear();
    dragPointerId = null;
    dragLastPoint = null;
    pinchStartDistance = 0;
    pinchStartMidpoint = null;
    unlockBody();
    // Restore focus for a11y without scrolling the page — `focus()` otherwise mimics scrollIntoView and fights `scrollTo(lockedScrollY)`.
    activeTrigger?.focus({ preventScroll: true });
    activeTrigger = null;
  };

  const close = () => {
    if (overlay.hidden || overlay.dataset.state === "closing") return;
    clearCloseTimer();
    overlay.dataset.state = "closing";
    closeTimer = window.setTimeout(finishClose, CLOSE_DURATION_MS);
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
    applyMainInertOnOpen();
    attachFocusTrap();
    lockBody();
    resetTransform();

    requestAnimationFrame(() => {
      overlay.dataset.state = "open";
      closeButton.focus();
    });
  };

  const onImageLoad = () => resetTransform();

  const onOverlayClick = (event: MouseEvent) => {
    if (event.target === overlay) close();
  };

  const onWheel = (event: WheelEvent) => {
    event.preventDefault();
    setTransform(scale + (event.deltaY < 0 ? WHEEL_STEP : -WHEEL_STEP));
  };

  const onPointerDown = (event: PointerEvent) => {
    pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
    viewport.setPointerCapture(event.pointerId);

    if (pointers.size === 2) {
      const [first, second] = Array.from(pointers.values());
      pinchStartDistance = getDistance(first, second);
      pinchStartScale = scale;
      pinchStartOffset = { x: offsetX, y: offsetY };
      pinchStartMidpoint = getMidpoint(first, second);
      dragPointerId = null;
      dragLastPoint = null;
      return;
    }

    if (scale > MIN_SCALE) {
      dragPointerId = event.pointerId;
      dragLastPoint = { x: event.clientX, y: event.clientY };
    }
  };

  const onPointerMove = (event: PointerEvent) => {
    if (!pointers.has(event.pointerId)) return;

    pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });

    if (pointers.size >= 2 && pinchStartMidpoint) {
      const [first, second] = Array.from(pointers.values());
      const currentDistance = getDistance(first, second);
      const currentMidpoint = getMidpoint(first, second);
      const nextScale = pinchStartDistance > 0 ? pinchStartScale * (currentDistance / pinchStartDistance) : scale;
      const nextOffsetX = pinchStartOffset.x + (currentMidpoint.x - pinchStartMidpoint.x);
      const nextOffsetY = pinchStartOffset.y + (currentMidpoint.y - pinchStartMidpoint.y);
      setTransform(nextScale, nextOffsetX, nextOffsetY);
      return;
    }

    if (dragPointerId !== event.pointerId || !dragLastPoint || scale <= MIN_SCALE) return;

    const deltaX = event.clientX - dragLastPoint.x;
    const deltaY = event.clientY - dragLastPoint.y;
    dragLastPoint = { x: event.clientX, y: event.clientY };
    setTransform(scale, offsetX + deltaX, offsetY + deltaY);
  };

  const onPointerEnd = (event: PointerEvent) => {
    pointers.delete(event.pointerId);

    if (viewport.hasPointerCapture(event.pointerId)) {
      viewport.releasePointerCapture(event.pointerId);
    }

    if (dragPointerId === event.pointerId) {
      dragPointerId = null;
      dragLastPoint = null;
    }

    if (pointers.size < 2) {
      pinchStartDistance = 0;
      pinchStartMidpoint = null;
    }

    if (pointers.size === 1 && scale > MIN_SCALE) {
      const [remainingPointerId, remainingPoint] = Array.from(pointers.entries())[0];
      dragPointerId = remainingPointerId;
      dragLastPoint = remainingPoint;
    }
  };

  const onViewportDoubleClick = () => {
    setTransform(scale > MIN_SCALE ? MIN_SCALE : 2);
  };

  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key === "Tab") {
      event.preventDefault();
      closeButton.focus();
      return;
    }

    if (event.key === "Escape") {
      event.preventDefault();
      close();
      return;
    }

    if (event.key === "+" || event.key === "=") {
      event.preventDefault();
      setTransform(scale + WHEEL_STEP);
      return;
    }

    if (event.key === "-" || event.key === "_") {
      event.preventDefault();
      setTransform(scale - WHEEL_STEP);
      return;
    }

    if (event.key === "0") {
      event.preventDefault();
      resetTransform();
    }
  };

  closeButton.addEventListener("click", close);
  overlay.addEventListener("click", onOverlayClick);
  overlay.addEventListener("keydown", onKeyDown);
  viewport.addEventListener("wheel", onWheel, { passive: false });
  viewport.addEventListener("pointerdown", onPointerDown);
  viewport.addEventListener("pointermove", onPointerMove);
  viewport.addEventListener("pointerup", onPointerEnd);
  viewport.addEventListener("pointercancel", onPointerEnd);
  viewport.addEventListener("pointerleave", onPointerEnd);
  viewport.addEventListener("dblclick", onViewportDoubleClick);
  image.addEventListener("load", onImageLoad);

  const removeAllListeners = () => {
    closeButton.removeEventListener("click", close);
    overlay.removeEventListener("click", onOverlayClick);
    overlay.removeEventListener("keydown", onKeyDown);
    viewport.removeEventListener("wheel", onWheel);
    viewport.removeEventListener("pointerdown", onPointerDown);
    viewport.removeEventListener("pointermove", onPointerMove);
    viewport.removeEventListener("pointerup", onPointerEnd);
    viewport.removeEventListener("pointercancel", onPointerEnd);
    viewport.removeEventListener("pointerleave", onPointerEnd);
    viewport.removeEventListener("dblclick", onViewportDoubleClick);
    image.removeEventListener("load", onImageLoad);
  };

  const syncTeardown = () => {
    clearCloseTimer();
    detachFocusTrap();
    restoreMainInertAfterClose();
    if (!overlay.hidden) {
      overlay.hidden = true;
      overlay.dataset.state = "closed";
      overlay.setAttribute("aria-hidden", "true");
      image.removeAttribute("src");
      resetTransform();
      pointers.clear();
      dragPointerId = null;
      dragLastPoint = null;
      pinchStartDistance = 0;
      pinchStartMidpoint = null;
      unlockBody();
      activeTrigger?.focus({ preventScroll: true });
      activeTrigger = null;
    }
  };

  return {
    open,
    destroy: () => {
      syncTeardown();
      removeAllListeners();
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
    image.classList.add(...LIGHTBOX_TRIGGER_IMAGE_CLASS.split(" "));

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
      image.classList.remove(...LIGHTBOX_TRIGGER_IMAGE_CLASS.split(" "));
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
