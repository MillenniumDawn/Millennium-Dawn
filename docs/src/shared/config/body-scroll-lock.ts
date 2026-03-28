/**
 * CSS class applied to `document.body` while the TOC mobile drawer locks scroll.
 * The image lightbox checks this when restoring `inert` on `#main-content` so an open drawer stays correct.
 */
export const TOC_DRAWER_BODY_LOCK_CLASS = "toc-lock" as const;
