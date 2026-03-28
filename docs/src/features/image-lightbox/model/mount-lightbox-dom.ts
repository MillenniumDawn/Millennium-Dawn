import {
  LIGHTBOX_CLOSE_BUTTON_CLASS,
  LIGHTBOX_CONTENT_CLASS,
  LIGHTBOX_IMAGE_CLASS,
  LIGHTBOX_OVERLAY_CLASS,
  LIGHTBOX_VIEWPORT_CLASS,
} from "@/shared/ui/tailwind";
import { LIGHTBOX_TITLE_ID } from "./constants";

export interface LightboxDomRefs {
  overlay: HTMLElement;
  titleEl: HTMLHeadingElement;
  viewport: HTMLElement;
  image: HTMLImageElement;
  closeButton: HTMLButtonElement;
}

export function mountLightboxDom(): LightboxDomRefs | null {
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
    <h2 class="sr-only pointer-events-none absolute left-0 top-0 m-0 border-0 p-0" id="${LIGHTBOX_TITLE_ID}"></h2>
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

  return { overlay, titleEl, viewport, image, closeButton };
}
