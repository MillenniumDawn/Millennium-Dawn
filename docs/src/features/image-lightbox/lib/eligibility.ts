export const LIGHTBOX_EXCLUDE_CLOSEST_SELECTOR =
  "[data-lightbox-ignore], dialog, button, .site-header, .site-footer, picture[aria-hidden='true']";

export function isEligibleLightboxImage(image: HTMLImageElement): boolean {
  if (image.closest(LIGHTBOX_EXCLUDE_CLOSEST_SELECTOR)) return false;
  const src = image.currentSrc ?? image.getAttribute("src") ?? "";
  return Boolean(src.trim());
}
