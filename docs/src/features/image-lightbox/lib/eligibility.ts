export const LIGHTBOX_EXCLUDE_CLOSEST_SELECTOR =
  "[data-lightbox-ignore], dialog, button, .site-header, .site-footer, picture[aria-hidden='true']";

/** First non-empty URL among currentSrc, src, and the src attribute (avoids `??` treating `""` as a value). */
export function pickResolvedImageUrl(image: HTMLImageElement): string {
  for (const raw of [image.currentSrc, image.src, image.getAttribute("src")]) {
    if (typeof raw === "string" && raw.trim() !== "") return raw.trim();
  }
  return "";
}

export function isEligibleLightboxImage(image: HTMLImageElement): boolean {
  if (image.closest(LIGHTBOX_EXCLUDE_CLOSEST_SELECTOR)) return false;
  return pickResolvedImageUrl(image) !== "";
}
