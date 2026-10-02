export const MAIN_CONTENT_SELECTOR = "#main-content";
/** Scope lightbox to main content only (avoids header/footer chrome and duplicate work on large DOMs). */
export const CONTENT_IMAGE_SELECTOR = `${MAIN_CONTENT_SELECTOR} img`;
export const BOUND_ATTRIBUTE = "data-image-lightbox-bound";
export const LIGHTBOX_TITLE_ID = "image-lightbox-title";
export const MIN_SCALE = 1;
export const MAX_SCALE = 5;
export const WHEEL_STEP = 0.2;
export const CLOSE_DURATION_MS = 180;
export const SCROLL_TOP_CSS_VAR = "--lightbox-scroll-top";
export const SCROLLBAR_COMPENSATION_CSS_VAR = "--lightbox-scrollbar-compensation";
