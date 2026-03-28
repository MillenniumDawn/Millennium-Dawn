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

export function getLightboxBaseImageSize(
  image: HTMLImageElement,
  viewport: HTMLElement,
): { width: number; height: number } {
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
