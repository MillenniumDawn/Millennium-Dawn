export const TOC_IDS = {
  sidebar: "toc-sidebar",
  heading: "toc-heading",
  toggle: "toc-toggle",
  backdrop: "toc-backdrop",
  panel: "toc-panel",
  close: "toc-close",
  progress: "toc-progress",
  nav: "toc-nav",
} as const;

export const TOC_ATTRS = {
  tocId: "data-toc-id",
  link: "data-toc-link",
  expand: "data-toc-expand",
  sublist: "data-toc-sublist",
} as const;

export const TOC_STATES = {
  active: "is-active",
  expanded: "is-expanded",
} as const;

export const TOC_HEADING_RANGE = {
  minDepth: 2,
  maxDepth: 4,
} as const;

function buildHeadingSelector(minDepth: number, maxDepth: number): string {
  const selectors: string[] = [];

  for (let depth = minDepth; depth <= maxDepth; depth += 1) {
    selectors.push(`h${depth}`);
  }

  return selectors.join(", ");
}

export const TOC_SELECTORS = {
  content: ".main-content",
  header: ".site-header",
  footer: ".site-footer",
  link: `[${TOC_ATTRS.link}]`,
  expandButton: `[${TOC_ATTRS.expand}]`,
  headings: buildHeadingSelector(TOC_HEADING_RANGE.minDepth, TOC_HEADING_RANGE.maxDepth),
} as const;

export const TOC_LABELS = {
  title: "Contents",
  nav: "Page sections",
  open: "Open table of contents",
  close: "Close table of contents",
  expand: (text: string): string => `Expand: ${text}`,
} as const;

export const TOC_DEFAULTS = {
  scrollOffsetPx: 120,
  drawerAnimMs: 280,
  wideMin: "1100px",
  fallbackIdBase: "section",
} as const;

export const TOC_DRAWER = {
  bodyLockClass: "toc-lock",
  inertSelectors: ["#main-content", TOC_SELECTORS.header, TOC_SELECTORS.footer],
  openLabels: { expanded: "true", ariaLabel: TOC_LABELS.close },
  closedLabels: { expanded: "false", ariaLabel: TOC_LABELS.open },
  lockScroll: true,
} as const;
