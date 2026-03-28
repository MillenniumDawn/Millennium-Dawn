import { LIGHTBOX_FULL_SRC_ATTR } from "../../../shared/config/lightbox-dom";

export const LIGHTBOX_EXCLUDE_CLOSEST_SELECTOR =
  "[data-lightbox-ignore], dialog, button, .site-header, .site-footer, picture[aria-hidden='true']";

/**
 * Prefer full-resolution URL from markdown `Picture` (see `ResponsiveImage`) so zoom is not limited
 * to the responsive `srcset` candidate. Falls back to `currentSrc` / `src` for plain `<img>` etc.
 */
export function pickResolvedImageUrl(image: HTMLImageElement): string {
  const onImg = image.getAttribute(LIGHTBOX_FULL_SRC_ATTR)?.trim();
  if (onImg) return onImg;
  const parent = image.parentElement;
  if (parent?.tagName === "PICTURE") {
    const onPicture = parent.getAttribute(LIGHTBOX_FULL_SRC_ATTR)?.trim();
    if (onPicture) return onPicture;
  }

  for (const raw of [image.currentSrc, image.src, image.getAttribute("src")]) {
    if (typeof raw === "string" && raw.trim() !== "") return raw.trim();
  }
  return "";
}

export function isEligibleLightboxImage(image: HTMLImageElement): boolean {
  if (image.closest(LIGHTBOX_EXCLUDE_CLOSEST_SELECTOR)) return false;
  return pickResolvedImageUrl(image) !== "";
}
