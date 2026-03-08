import { createDrawer } from "../../../shared/lib/drawer";
import { readCssMsVar, readCssPxVar, readCssStringVar } from "../../../shared/lib/tokens";
import {
  TOC_ATTRS,
  TOC_CLASSES,
  TOC_DEFAULTS,
  TOC_DRAWER,
  TOC_IDS,
  TOC_SELECTORS,
} from "../lib/config";
import { ensureHeadingIds, queryTocHeadings } from "../lib/headingIds";
import { bindExpandButtons, buildTree, renderNav, toggleSublist } from "./dom";
import { initTocObserver } from "./observer";
import { initTocScroll } from "./scroll";
import type { TocEntry } from "./types";

type Cleanup = () => void;
type TocDrawer = ReturnType<typeof createDrawer>;

const NOOP: Cleanup = () => {};

interface TocDomRefs {
  sidebar: HTMLElement;
  panel: HTMLElement;
  nav: HTMLElement;
  toggle: HTMLElement;
  closeBtn: HTMLElement | null;
  backdrop: HTMLElement | null;
  progress: HTMLElement | null;
  content: HTMLElement;
}

interface TocRuntimeConfig {
  scrollOffset: number;
  drawerAnimMs: number;
  wideMin: string;
}

function hideToc(sidebar: HTMLElement | null): Cleanup {
  document.body.classList.remove("has-toc");
  if (sidebar) {
    sidebar.hidden = true;
  }

  return NOOP;
}

function readRuntimeConfig(): TocRuntimeConfig {
  return {
    scrollOffset: readCssPxVar("--toc-scroll-offset", TOC_DEFAULTS.scrollOffsetPx),
    drawerAnimMs: readCssMsVar("--duration-toc-drawer", TOC_DEFAULTS.drawerAnimMs),
    wideMin: readCssStringVar("--bp-wide-min", TOC_DEFAULTS.wideMin),
  };
}

function queryDomRefs(sidebar: HTMLElement | null): TocDomRefs | null {
  const panel = document.getElementById(TOC_IDS.panel);
  const nav = document.getElementById(TOC_IDS.nav);
  const toggle = document.getElementById(TOC_IDS.toggle);
  const content = document.querySelector<HTMLElement>(TOC_SELECTORS.content);

  if (!sidebar || !panel || !nav || !toggle || !content) {
    return null;
  }

  return {
    sidebar,
    panel,
    nav,
    toggle,
    content,
    closeBtn: document.getElementById(TOC_IDS.close),
    backdrop: document.getElementById(TOC_IDS.backdrop),
    progress: document.getElementById(TOC_IDS.progress),
  };
}

function hydrateNav(nav: HTMLElement, content: HTMLElement): { links: HTMLAnchorElement[]; cleanup: Cleanup } | null {
  let links = Array.from(nav.querySelectorAll<HTMLAnchorElement>(TOC_SELECTORS.link));
  let cleanupExpandButtons = NOOP;

  const rebindExpandButtons = () => {
    cleanupExpandButtons();
    cleanupExpandButtons = bindExpandButtons(nav);
  };

  if (!links.length) {
    const headings = queryTocHeadings(content);
    if (!headings.length) {
      cleanupExpandButtons();
      return null;
    }

    ensureHeadingIds(headings);
    renderNav(nav, buildTree(headings));
  }

  rebindExpandButtons();
  links = Array.from(nav.querySelectorAll<HTMLAnchorElement>(TOC_SELECTORS.link));

  return {
    links,
    cleanup: () => cleanupExpandButtons(),
  };
}

function buildHeadingRegistry(links: HTMLAnchorElement[]): {
  headingEntries: TocEntry[];
  entryById: Record<string, TocEntry>;
} | null {
  const headingEntries: TocEntry[] = [];
  const entryById: Record<string, TocEntry> = {};

  links.forEach((link) => {
    const id = link.getAttribute(TOC_ATTRS.tocId);
    if (!id) return;

    const headingEl = document.getElementById(id);
    if (!(headingEl instanceof HTMLElement)) return;

    const entry: TocEntry = { el: headingEl, link };
    headingEntries.push(entry);
    entryById[id] = entry;
  });

  if (!headingEntries.length) {
    return null;
  }

  return { headingEntries, entryById };
}

function createActiveState(nav: HTMLElement): {
  setActive: (nextActive: TocEntry | null) => void;
  autoExpandAncestors: (link: HTMLElement) => void;
} {
  let currentActive: TocEntry | null = null;

  const autoExpandAncestors = (link: HTMLElement) => {
    let node = link.parentElement;
    while (node && node !== nav) {
      if (node.classList.contains(TOC_CLASSES.sublist) && !node.classList.contains(TOC_CLASSES.expanded)) {
        const idx = node.getAttribute(TOC_ATTRS.sublist);
        if (!idx) {
          node = node.parentElement;
          continue;
        }

        const button = nav.querySelector<HTMLElement>(`[${TOC_ATTRS.expand}="${idx}"]`);
        if (button) {
          toggleSublist(button, node, true);
        }
      }
      node = node.parentElement;
    }
  };

  const scrollTocIntoView = (link: HTMLElement) => {
    const navRect = nav.getBoundingClientRect();
    const linkRect = link.getBoundingClientRect();

    if (linkRect.top < navRect.top || linkRect.bottom > navRect.bottom) {
      link.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
  };

  return {
    autoExpandAncestors,
    setActive(nextActive) {
      if (nextActive === currentActive) return;

      if (currentActive) {
        currentActive.link.classList.remove(TOC_CLASSES.active);
        currentActive.link.removeAttribute("aria-current");
      }

      currentActive = nextActive;

      if (currentActive) {
        currentActive.link.classList.add(TOC_CLASSES.active);
        currentActive.link.setAttribute("aria-current", "location");
        autoExpandAncestors(currentActive.link);
        scrollTocIntoView(currentActive.link);
      }
    },
  };
}

function createPanelSemanticsController(panel: HTMLElement): (dialogMode: boolean) => void {
  return (dialogMode) => {
    panel.setAttribute("role", dialogMode ? "dialog" : "region");
    if (dialogMode) {
      panel.setAttribute("aria-modal", "true");
    } else {
      panel.removeAttribute("aria-modal");
    }
  };
}

function createTocDrawer(dom: TocDomRefs, config: TocRuntimeConfig, setPanelSemantics: (dialogMode: boolean) => void) {
  return createDrawer({
    container: dom.sidebar,
    panel: dom.panel,
    toggle: dom.toggle,
    closeBtn: dom.closeBtn,
    backdrop: dom.backdrop,
    desktopMQ: window.matchMedia(`(min-width: ${config.wideMin})`),
    animMs: config.drawerAnimMs,
    bodyLockClass: TOC_DRAWER.bodyLockClass,
    openLabels: TOC_DRAWER.openLabels,
    closedLabels: TOC_DRAWER.closedLabels,
    lockScroll: TOC_DRAWER.lockScroll,
    inertSelectors: [...TOC_DRAWER.inertSelectors],
    onOpen: () => setPanelSemantics(true),
    onClose: () => setPanelSemantics(false),
  });
}

function bindCloseDrawerOnNavClick(nav: HTMLElement, drawer: TocDrawer): Cleanup {
  const onNavLinkCloseDrawer = (event: MouseEvent) => {
    if (event.target instanceof Element && event.target.closest(TOC_SELECTORS.link) && drawer.isOpen()) {
      drawer.close(false);
    }
  };

  nav.addEventListener("click", onNavLinkCloseDrawer);
  return () => nav.removeEventListener("click", onNavLinkCloseDrawer);
}

function restoreHashExpansion(nav: HTMLElement, autoExpandAncestors: (link: HTMLElement) => void): void {
  if (!window.location.hash) {
    return;
  }

  try {
    const hashId = window.location.hash.slice(1);
    const hashLink = nav.querySelector<HTMLElement>(`[${TOC_ATTRS.tocId}="${hashId}"]`);
    if (hashLink) {
      autoExpandAncestors(hashLink);
    }
  } catch {
    // Ignore malformed hash selectors.
  }
}

export function initToc(): Cleanup {
  const sidebar = document.getElementById(TOC_IDS.sidebar);

  if (document.body.dataset.toc === "off") {
    return hideToc(sidebar);
  }

  const dom = queryDomRefs(sidebar);
  if (!dom) {
    return NOOP;
  }

  const config = readRuntimeConfig();
  const navState = hydrateNav(dom.nav, dom.content);
  if (!navState) {
    return hideToc(dom.sidebar);
  }

  const registry = buildHeadingRegistry(navState.links);
  if (!registry) {
    navState.cleanup();
    return hideToc(dom.sidebar);
  }

  dom.sidebar.hidden = false;
  document.body.classList.add("has-toc");

  const { setActive, autoExpandAncestors } = createActiveState(dom.nav);
  const setPanelSemantics = createPanelSemanticsController(dom.panel);
  setPanelSemantics(false);

  const drawer = createTocDrawer(dom, config, setPanelSemantics);
  const cleanupNavDrawerClose = bindCloseDrawerOnNavClick(dom.nav, drawer);
  const observerHandle = initTocObserver(registry.headingEntries, registry.entryById, config.scrollOffset, setActive);
  const scrollHandle = initTocScroll(dom.nav, dom.progress, config.scrollOffset);

  restoreHashExpansion(dom.nav, autoExpandAncestors);

  return () => {
    observerHandle.cleanup();
    scrollHandle.cleanup();
    drawer.cleanup();
    navState.cleanup();
    cleanupNavDrawerClose();
    setPanelSemantics(false);
  };
}
