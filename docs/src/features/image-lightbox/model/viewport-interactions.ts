import {
  clampLightbox,
  getLightboxBaseImageSize,
  lightboxDistance,
  lightboxMidpoint,
  type LightboxPoint,
} from "../lib/lightbox-geometry";
import { MIN_SCALE, MAX_SCALE, WHEEL_STEP } from "./constants";

/** Mirrors `getLightboxContentContainer` + client sizes in `lightbox-geometry.ts` (local helper avoids ESLint `no-unsafe-*` on that import). */
function lightboxContentBoxSize(image: HTMLImageElement, viewport: HTMLElement): { width: number; height: number } {
  const parent = image.parentElement;
  if (parent instanceof HTMLElement && parent.hasAttribute("data-image-lightbox-content")) {
    return { width: parent.clientWidth, height: parent.clientHeight };
  }
  return { width: viewport.clientWidth, height: viewport.clientHeight };
}

export interface ViewportInteractionsOptions {
  overlay: HTMLElement;
  viewport: HTMLElement;
  image: HTMLImageElement;
  closeButton: HTMLButtonElement;
  requestClose: () => void;
}

export interface ViewportInteractions {
  resetTransform: () => void;
  resetPointerState: () => void;
  bind: () => void;
  unbind: () => void;
}

export function createViewportInteractions(opts: ViewportInteractionsOptions): ViewportInteractions {
  const { overlay, viewport, image, closeButton, requestClose } = opts;

  let scale = MIN_SCALE;
  let offsetX = 0;
  let offsetY = 0;
  let dragPointerId: number | null = null;
  let dragLastPoint: LightboxPoint | null = null;
  let pinchStartDistance = 0;
  let pinchStartScale = MIN_SCALE;
  let pinchStartOffset = { x: 0, y: 0 };
  let pinchStartMidpoint: LightboxPoint | null = null;
  const pointers = new Map<number, LightboxPoint>();

  const clampOffsets = (nextScale: number, nextOffsetX: number, nextOffsetY: number) => {
    const baseSize = getLightboxBaseImageSize(image, viewport);
    const scaledWidth = baseSize.width * nextScale;
    const scaledHeight = baseSize.height * nextScale;
    const { width: boxW, height: boxH } = lightboxContentBoxSize(image, viewport);
    const maxOffsetX = Math.max(0, (scaledWidth - boxW) * 0.5);
    const maxOffsetY = Math.max(0, (scaledHeight - boxH) * 0.5);

    return {
      x: clampLightbox(nextOffsetX, -maxOffsetX, maxOffsetX),
      y: clampLightbox(nextOffsetY, -maxOffsetY, maxOffsetY),
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
    scale = clampLightbox(Number(nextScale.toFixed(3)), MIN_SCALE, MAX_SCALE);
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

  const resetPointerState = () => {
    pointers.clear();
    dragPointerId = null;
    dragLastPoint = null;
    pinchStartDistance = 0;
    pinchStartMidpoint = null;
  };

  const onImageLoad = () => resetTransform();

  const onWheel = (event: WheelEvent) => {
    event.preventDefault();
    setTransform(scale + (event.deltaY < 0 ? WHEEL_STEP : -WHEEL_STEP));
  };

  const onPointerDown = (event: PointerEvent) => {
    pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
    viewport.setPointerCapture(event.pointerId);

    if (pointers.size === 2) {
      const [first, second] = Array.from(pointers.values());
      pinchStartDistance = lightboxDistance(first, second);
      pinchStartScale = scale;
      pinchStartOffset = { x: offsetX, y: offsetY };
      pinchStartMidpoint = lightboxMidpoint(first, second);
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
      const currentDistance = lightboxDistance(first, second);
      const currentMidpoint = lightboxMidpoint(first, second);
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

  const onImageDoubleClick = () => {
    setTransform(scale > MIN_SCALE ? MIN_SCALE : 2);
  };

  const onBackdropClick = (event: MouseEvent) => {
    const t = event.target;
    if (!(t instanceof Node)) return;
    if (!viewport.contains(t)) return;
    if (image.contains(t)) return;
    requestClose();
  };

  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key === "Tab") {
      event.preventDefault();
      closeButton.focus();
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

  const bind = () => {
    viewport.addEventListener("wheel", onWheel, { passive: false });
    viewport.addEventListener("pointerdown", onPointerDown);
    viewport.addEventListener("pointermove", onPointerMove);
    viewport.addEventListener("pointerup", onPointerEnd);
    viewport.addEventListener("pointercancel", onPointerEnd);
    viewport.addEventListener("lostpointercapture", onPointerEnd);
    viewport.addEventListener("click", onBackdropClick);
    image.addEventListener("dblclick", onImageDoubleClick);
    image.addEventListener("load", onImageLoad);
    overlay.addEventListener("keydown", onKeyDown);
  };

  const unbind = () => {
    viewport.removeEventListener("wheel", onWheel);
    viewport.removeEventListener("pointerdown", onPointerDown);
    viewport.removeEventListener("pointermove", onPointerMove);
    viewport.removeEventListener("pointerup", onPointerEnd);
    viewport.removeEventListener("pointercancel", onPointerEnd);
    viewport.removeEventListener("lostpointercapture", onPointerEnd);
    viewport.removeEventListener("click", onBackdropClick);
    image.removeEventListener("dblclick", onImageDoubleClick);
    image.removeEventListener("load", onImageLoad);
    overlay.removeEventListener("keydown", onKeyDown);
  };

  return {
    resetTransform,
    resetPointerState,
    bind,
    unbind,
  };
}
