export interface LightboxPoint {
  x: number;
  y: number;
}

export function clampLightbox(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

export function lightboxDistance(first: LightboxPoint, second: LightboxPoint): number {
  return Math.hypot(second.x - first.x, second.y - first.y);
}

export function lightboxMidpoint(first: LightboxPoint, second: LightboxPoint): LightboxPoint {
  return {
    x: (first.x + second.x) / 2,
    y: (first.y + second.y) / 2,
  };
}

/** Content wrapper inside padded viewport — use for fit/pan math, not full `viewport.clientWidth`. */
export function getLightboxContentContainer(image: HTMLImageElement, viewport: HTMLElement): HTMLElement {
  const parent = image.parentElement;
  if (parent instanceof HTMLElement && parent.hasAttribute("data-image-lightbox-content")) {
    return parent;
  }
  return viewport;
}

/** Fits the image inside the content box (inside viewport padding) so mobile insets stay symmetric. */
export function getLightboxBaseImageSize(
  image: HTMLImageElement,
  viewport: HTMLElement,
): { width: number; height: number } {
  const naturalWidth = image.naturalWidth || viewport.clientWidth || 1;
  const naturalHeight = image.naturalHeight || viewport.clientHeight || 1;
  const fitEl = getLightboxContentContainer(image, viewport);
  const viewportWidth = fitEl.clientWidth || naturalWidth;
  const viewportHeight = fitEl.clientHeight || naturalHeight;
  const fitRatio = Math.min(viewportWidth / naturalWidth, viewportHeight / naturalHeight, 1);

  return {
    width: naturalWidth * fitRatio,
    height: naturalHeight * fitRatio,
  };
}
