type Cleanup = () => void;

const NOOP: Cleanup = () => {};

const ROOT_SELECTOR = "[data-dev-diary-root]";
const GALLERY_SELECTOR = ".dev-diary-gallery";
const TRIGGER_SELECTOR = "[data-content-media-trigger]";
const MIN_ZOOM = 1;
const MAX_ZOOM = 3;
const ZOOM_STEP = 0.25;

const GALLERY_CLASS = [
  "grid",
  "w-full",
  "grid-cols-1",
  "gap-md",
  "my-lg",
  "tablet:grid-cols-2",
].join(" ");

const MEDIA_FIGURE_CLASS = [
  "my-lg",
  "grid",
  "w-full",
  "max-w-[64rem]",
  "gap-[0.7rem]",
  "mx-auto",
].join(" ");

const MEDIA_GALLERY_ITEM_CLASS = [
  "m-0",
  "grid",
  "w-full",
  "gap-[0.7rem]",
].join(" ");

const MEDIA_TRIGGER_CLASS = [
  "block",
  "w-full",
  "cursor-zoom-in",
  "overflow-hidden",
  "rounded-[18px]",
  "border-0",
  "bg-transparent",
  "p-0",
  "shadow-sm",
  "transition-[transform,box-shadow]",
  "duration-200",
  "ease-out",
  "hover:-translate-y-0.5",
  "hover:shadow-md",
  "focus-visible:[outline:var(--focus-ring-width)_solid_var(--focus-ring-color)]",
  "focus-visible:[outline-offset:3px]",
].join(" ");

const MEDIA_IMAGE_CLASS = [
  "block",
  "w-full",
  "h-auto",
  "max-h-[min(70vh,42rem)]",
  "rounded-[18px]",
  "bg-surface",
  "object-contain",
].join(" ");

const MEDIA_CAPTION_CLASS = [
  "m-0",
  "text-[0.95rem]",
  "leading-[1.6]",
  "text-text-secondary",
].join(" ");

const LIGHTBOX_DIALOG_CLASS = [
  "m-auto",
  "w-[min(96vw,1200px)]",
  "max-w-none",
  "max-h-none",
  "border-0",
  "bg-transparent",
  "p-0",
  "[&[open]]:grid",
  "[&[open]]:place-items-center",
  "[&::backdrop]:bg-[rgba(12,18,30,0.82)]",
  "[&::backdrop]:backdrop-blur-[8px]",
  "phone:w-screen",
].join(" ");

const LIGHTBOX_SURFACE_CLASS = ["relative", "w-full"].join(" ");

const LIGHTBOX_FRAME_CLASS = [
  "grid",
  "gap-[0.875rem]",
  "rounded-[24px]",
  "border",
  "border-[color-mix(in_srgb,var(--color-border)_55%,transparent)]",
  "bg-[linear-gradient(180deg,color-mix(in_srgb,var(--color-surface)_96%,transparent),color-mix(in_srgb,var(--color-surface)_92%,transparent))]",
  "p-[clamp(1rem,1vw+0.75rem,1.5rem)]",
  "shadow-lg",
  "backdrop-blur-[12px]",
  "backdrop-saturate-[1.1]",
].join(" ");

const LIGHTBOX_TOOLBAR_CLASS = [
  "flex",
  "items-center",
  "justify-between",
  "gap-md",
  "phone:flex-wrap",
].join(" ");

const LIGHTBOX_TOOLS_CLASS = [
  "inline-flex",
  "items-center",
  "gap-2",
  "rounded-full",
  "border",
  "border-[color-mix(in_srgb,var(--color-border)_60%,transparent)]",
  "bg-[color-mix(in_srgb,var(--color-surface)_82%,transparent)]",
  "p-[0.35rem]",
  "shadow-sm",
  "phone:order-2",
].join(" ");

const LIGHTBOX_TOOL_CLASS = [
  "inline-flex",
  "min-w-10",
  "h-10",
  "items-center",
  "justify-center",
  "rounded-full",
  "border-0",
  "bg-transparent",
  "px-[0.8rem]",
  "text-base",
  "font-bold",
  "text-text",
  "transition-[background-color,color,opacity]",
  "duration-200",
  "ease-out",
  "enabled:hover:bg-[color-mix(in_srgb,var(--color-primary-light)_72%,var(--color-surface))]",
  "enabled:hover:text-primary",
  "disabled:opacity-45",
  "focus-visible:[outline:var(--focus-ring-width)_solid_var(--focus-ring-color)]",
  "focus-visible:[outline-offset:2px]",
].join(" ");

const LIGHTBOX_CLOSE_CLASS = [
  "inline-flex",
  "size-11",
  "items-center",
  "justify-center",
  "rounded-full",
  "border-0",
  "bg-[color-mix(in_srgb,var(--color-surface)_82%,transparent)]",
  "text-text",
  "text-[1.8rem]",
  "leading-none",
  "shadow-sm",
  "cursor-pointer",
  "phone:order-1",
  "phone:ml-auto",
  "focus-visible:[outline:var(--focus-ring-width)_solid_var(--focus-ring-color)]",
  "focus-visible:[outline-offset:2px]",
].join(" ");

const LIGHTBOX_VIEWPORT_CLASS = [
  "grid",
  "max-h-[calc(100vh-10.5rem)]",
  "place-items-center",
  "overflow-auto",
  "rounded-[20px]",
  "bg-[radial-gradient(circle_at_top,color-mix(in_srgb,var(--color-primary-light)_40%,transparent),transparent_50%),color-mix(in_srgb,var(--color-bg)_92%,black_8%)]",
  "p-3",
  "cursor-zoom-in",
].join(" ");

const LIGHTBOX_IMAGE_CLASS = [
  "block",
  "w-auto",
  "max-w-full",
  "max-h-[calc(100vh-12rem)]",
  "select-none",
  "rounded-[18px]",
  "bg-transparent",
  "object-contain",
  "transition-transform",
  "duration-200",
  "ease-out",
  "[transform-origin:center_center]",
  "data-[zoomed=true]:cursor-zoom-out",
].join(" ");

const LIGHTBOX_CAPTION_CLASS = [
  "m-0",
  "pr-12",
  "text-[0.95rem]",
  "leading-[1.6]",
  "text-text-secondary",
].join(" ");

const LIGHTBOX_HINT_CLASS = [
  "m-0",
  "text-[0.85rem]",
  "leading-[1.5]",
  "text-text-muted",
].join(" ");

function addClassesToElement(element: Element, classNames: string): void {
  classNames.split(/\s+/).filter(Boolean).forEach((className) => element.classList.add(className));
}

function getAll<T extends Element>(root: ParentNode, selector: string): T[] {
  return Array.from(root.querySelectorAll<T>(selector));
}

function isHTMLElement(value: Element | null): value is HTMLElement {
  return value instanceof HTMLElement;
}

function isStandaloneParagraph(parent: Element | null): parent is HTMLParagraphElement {
  return parent instanceof HTMLParagraphElement
    && parent.childElementCount === 1
    && parent.firstElementChild instanceof HTMLImageElement
    && (parent.textContent?.trim() ?? "") === "";
}

function upgradeImage(image: HTMLImageElement): void {
  if (image.closest(TRIGGER_SELECTOR)) return;

  const src = image.currentSrc || image.getAttribute("src");
  if (!src) return;

  const alt = image.getAttribute("alt")?.trim() ?? "";
  const parent = image.parentElement;
  const inGallery = isHTMLElement(parent) && parent.classList.contains("dev-diary-gallery");

  addClassesToElement(image, MEDIA_IMAGE_CLASS);
  if (!image.hasAttribute("loading")) image.loading = "lazy";
  image.decoding = "async";

  const figure = document.createElement("figure");
  figure.className = inGallery ? MEDIA_GALLERY_ITEM_CLASS : MEDIA_FIGURE_CLASS;

  const trigger = document.createElement("button");
  trigger.type = "button";
  trigger.className = MEDIA_TRIGGER_CLASS;
  trigger.dataset.contentMediaTrigger = "true";
  trigger.dataset.contentMediaSrc = src;
  trigger.dataset.contentMediaAlt = alt;
  trigger.setAttribute("aria-label", alt ? `Expand image: ${alt}` : "Expand image");

  if (alt) {
    const caption = document.createElement("figcaption");
    caption.className = MEDIA_CAPTION_CLASS;
    caption.textContent = alt;
    figure.append(caption);
  }

  if (isStandaloneParagraph(parent)) {
    parent.replaceWith(figure);
  } else {
    image.replaceWith(figure);
  }

  trigger.append(image);
  figure.prepend(trigger);
}

function createLightbox() {
  const dialog = document.createElement("dialog");
  dialog.className = LIGHTBOX_DIALOG_CLASS;
  dialog.dataset.contentMediaDialog = "true";
  dialog.innerHTML = `
    <div class="${LIGHTBOX_SURFACE_CLASS}">
      <div class="${LIGHTBOX_FRAME_CLASS}">
        <div class="${LIGHTBOX_TOOLBAR_CLASS}" aria-label="Image viewer controls">
          <div class="${LIGHTBOX_TOOLS_CLASS}">
            <button class="${LIGHTBOX_TOOL_CLASS}" type="button" aria-label="Zoom out" data-content-media-zoom-out>
              <span aria-hidden="true">−</span>
            </button>
            <button class="${LIGHTBOX_TOOL_CLASS}" type="button" aria-label="Reset zoom" data-content-media-zoom-reset>
              <span data-content-media-zoom-label>100%</span>
            </button>
            <button class="${LIGHTBOX_TOOL_CLASS}" type="button" aria-label="Zoom in" data-content-media-zoom-in>
              <span aria-hidden="true">+</span>
            </button>
          </div>

          <button class="${LIGHTBOX_CLOSE_CLASS}" type="button" aria-label="Close image viewer" data-content-media-close>
            <span aria-hidden="true">×</span>
          </button>
        </div>

        <div class="${LIGHTBOX_VIEWPORT_CLASS}" data-content-media-viewport>
          <img class="${LIGHTBOX_IMAGE_CLASS}" alt="" data-content-media-image />
        </div>
        <p class="${LIGHTBOX_CAPTION_CLASS}" hidden data-content-media-caption></p>
        <p class="${LIGHTBOX_HINT_CLASS}">Use mouse wheel or buttons to zoom. Press 0 to reset.</p>
      </div>
    </div>
  `;

  document.body.append(dialog);

  const image = dialog.querySelector<HTMLImageElement>("[data-content-media-image]");
  const caption = dialog.querySelector<HTMLElement>("[data-content-media-caption]");
  const closeButton = dialog.querySelector<HTMLButtonElement>("[data-content-media-close]");
  const viewport = dialog.querySelector<HTMLElement>("[data-content-media-viewport]");
  const zoomInButton = dialog.querySelector<HTMLButtonElement>("[data-content-media-zoom-in]");
  const zoomOutButton = dialog.querySelector<HTMLButtonElement>("[data-content-media-zoom-out]");
  const zoomResetButton = dialog.querySelector<HTMLButtonElement>("[data-content-media-zoom-reset]");
  const zoomLabel = dialog.querySelector<HTMLElement>("[data-content-media-zoom-label]");

  if (!image || !caption || !closeButton || !viewport || !zoomInButton || !zoomOutButton || !zoomResetButton || !zoomLabel) {
    dialog.remove();
    return null;
  }

  let lastActiveElement: HTMLElement | null = null;
  let zoom = MIN_ZOOM;

  const clampZoom = (value: number) => Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, value));

  const renderZoom = () => {
    image.style.transform = `scale(${zoom})`;
    image.dataset.zoomed = zoom > MIN_ZOOM ? "true" : "false";
    zoomLabel.textContent = `${Math.round(zoom * 100)}%`;
    zoomInButton.disabled = zoom >= MAX_ZOOM;
    zoomOutButton.disabled = zoom <= MIN_ZOOM;
  };

  const setZoom = (value: number) => {
    zoom = clampZoom(Number(value.toFixed(2)));
    renderZoom();
  };

  const resetZoom = () => setZoom(MIN_ZOOM);

  const close = () => {
    if (dialog.open) {
      dialog.close();
    }
    resetZoom();
    lastActiveElement?.focus();
    lastActiveElement = null;
  };

  const open = (src: string, alt: string, trigger: HTMLElement) => {
    resetZoom();
    image.src = src;
    image.alt = alt;
    caption.textContent = alt;
    caption.hidden = !alt;
    lastActiveElement = trigger;

    if (!dialog.open) {
      dialog.showModal();
    }
  };

  const onBackdropClick = (event: MouseEvent) => {
    if (event.target === dialog) close();
  };

  const onCloseClick = () => close();
  const onZoomInClick = () => setZoom(zoom + ZOOM_STEP);
  const onZoomOutClick = () => setZoom(zoom - ZOOM_STEP);
  const onZoomResetClick = () => resetZoom();
  const onViewportWheel = (event: WheelEvent) => {
    event.preventDefault();
    setZoom(zoom + (event.deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP));
  };
  const onImageDoubleClick = () => {
    setZoom(zoom > MIN_ZOOM ? MIN_ZOOM : 2);
  };
  const onDialogKeydown = (event: KeyboardEvent) => {
    if (event.key === "+" || event.key === "=") {
      event.preventDefault();
      onZoomInClick();
      return;
    }

    if (event.key === "-" || event.key === "_") {
      event.preventDefault();
      onZoomOutClick();
      return;
    }

    if (event.key === "0") {
      event.preventDefault();
      onZoomResetClick();
    }
  };

  dialog.addEventListener("click", onBackdropClick);
  dialog.addEventListener("keydown", onDialogKeydown);
  closeButton.addEventListener("click", onCloseClick);
  zoomInButton.addEventListener("click", onZoomInClick);
  zoomOutButton.addEventListener("click", onZoomOutClick);
  zoomResetButton.addEventListener("click", onZoomResetClick);
  viewport.addEventListener("wheel", onViewportWheel, { passive: false });
  image.addEventListener("dblclick", onImageDoubleClick);
  renderZoom();

  return {
    open,
    destroy: () => {
      dialog.removeEventListener("click", onBackdropClick);
      dialog.removeEventListener("keydown", onDialogKeydown);
      closeButton.removeEventListener("click", onCloseClick);
      zoomInButton.removeEventListener("click", onZoomInClick);
      zoomOutButton.removeEventListener("click", onZoomOutClick);
      zoomResetButton.removeEventListener("click", onZoomResetClick);
      viewport.removeEventListener("wheel", onViewportWheel);
      image.removeEventListener("dblclick", onImageDoubleClick);
      if (dialog.open) dialog.close();
      dialog.remove();
    },
  };
}

export function initContentMediaLightbox(): Cleanup {
  const roots = getAll<HTMLElement>(document, ROOT_SELECTOR);
  if (!roots.length) return NOOP;

  roots.forEach((root) => {
    getAll<HTMLElement>(root, GALLERY_SELECTOR).forEach((gallery) => {
      gallery.dataset.contentMediaGallery = "true";
      addClassesToElement(gallery, GALLERY_CLASS);
    });

    getAll<HTMLImageElement>(root, "img").forEach((image) => {
      upgradeImage(image);
    });
  });

  const triggers = getAll<HTMLElement>(document, TRIGGER_SELECTOR);
  if (!triggers.length) return NOOP;

  const lightbox = createLightbox();
  if (!lightbox) return NOOP;

  const onTriggerClick = (event: Event) => {
    const trigger = event.currentTarget;
    if (!(trigger instanceof HTMLElement)) return;

    const src = trigger.dataset.contentMediaSrc;
    if (!src) return;

    lightbox.open(src, trigger.dataset.contentMediaAlt ?? "", trigger);
  };

  triggers.forEach((trigger) => trigger.addEventListener("click", onTriggerClick));

  return () => {
    triggers.forEach((trigger) => trigger.removeEventListener("click", onTriggerClick));
    lightbox.destroy();
  };
}