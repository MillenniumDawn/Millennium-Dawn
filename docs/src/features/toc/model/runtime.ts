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

const NOOP: Cleanup = () => {};

export function initToc(): Cleanup {
  const sidebar = document.getElementById(TOC_IDS.sidebar);

  if (document.body.dataset.toc === "off") {
    document.body.classList.remove("has-toc");
    if (sidebar) sidebar.hidden = true;
    return NOOP;
  }

  const scrollOffset = readCssPxVar("--toc-scroll-offset", TOC_DEFAULTS.scrollOffsetPx);
  const drawerAnimMs = readCssMsVar("--duration-toc-drawer", TOC_DEFAULTS.drawerAnimMs);
  const wideMin = readCssStringVar("--bp-wide-min", TOC_DEFAULTS.wideMin);

  const panel = document.getElementById(TOC_IDS.panel);
  const nav = document.getElementById(TOC_IDS.nav);
  const toggle = document.getElementById(TOC_IDS.toggle);
  const closeBtn = document.getElementById(TOC_IDS.close);
  const backdrop = document.getElementById(TOC_IDS.backdrop);
  const progress = document.getElementById(TOC_IDS.progress);
  if (!sidebar || !panel || !nav || !toggle) return NOOP;

  const content = document.querySelector<HTMLElement>(TOC_SELECTORS.content);
  if (!content) return NOOP;

  let allLinks = Array.from(nav.querySelectorAll<HTMLAnchorElement>(TOC_SELECTORS.link));
  let cleanupExpandButtons = NOOP;

  const rebindExpandButtons = () => {
    cleanupExpandButtons();
    cleanupExpandButtons = bindExpandButtons(nav);
  };

  if (!allLinks.length) {
    const headings = queryTocHeadings(content);
    if (!headings.length) {
      document.body.classList.remove("has-toc");
      sidebar.hidden = true;
      return NOOP;
    }

    ensureHeadingIds(headings);
    renderNav(nav, buildTree(headings));
    rebindExpandButtons();
    allLinks = Array.from(nav.querySelectorAll<HTMLAnchorElement>(TOC_SELECTORS.link));
  } else {
    rebindExpandButtons();
  }

  sidebar.hidden = false;
  document.body.classList.add("has-toc");

  const headingEntries: TocEntry[] = [];
  const entryById: Record<string, TocEntry> = {};
  let currentActive: TocEntry | null = null;

  allLinks.forEach((link) => {
    const id = link.getAttribute(TOC_ATTRS.tocId);
    if (!id) return;

    const headingEl = document.getElementById(id);
    if (!(headingEl instanceof HTMLElement)) return;

    const entry: TocEntry = { el: headingEl, link };
    headingEntries.push(entry);
    entryById[id] = entry;
  });

  if (!headingEntries.length) {
    cleanupExpandButtons();
    document.body.classList.remove("has-toc");
    sidebar.hidden = true;
    return NOOP;
  }

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
        if (button) toggleSublist(button, node, true);
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

  const setActive = (nextActive: TocEntry | null) => {
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
  };

  const setPanelSemantics = (dialogMode: boolean) => {
    panel.setAttribute("role", dialogMode ? "dialog" : "region");
    if (dialogMode) {
      panel.setAttribute("aria-modal", "true");
    } else {
      panel.removeAttribute("aria-modal");
    }
  };

  setPanelSemantics(false);

  const drawer = createDrawer({
    container: sidebar,
    panel,
    toggle,
    closeBtn,
    backdrop,
    desktopMQ: window.matchMedia(`(min-width: ${wideMin})`),
    animMs: drawerAnimMs,
    bodyLockClass: TOC_DRAWER.bodyLockClass,
    openLabels: TOC_DRAWER.openLabels,
    closedLabels: TOC_DRAWER.closedLabels,
    lockScroll: TOC_DRAWER.lockScroll,
    inertSelectors: [...TOC_DRAWER.inertSelectors],
    onOpen: () => setPanelSemantics(true),
    onClose: () => setPanelSemantics(false),
  });

  const onNavLinkCloseDrawer = (event: MouseEvent) => {
    if (event.target instanceof Element && event.target.closest(TOC_SELECTORS.link) && drawer.isOpen()) {
      drawer.close(false);
    }
  };
  nav.addEventListener("click", onNavLinkCloseDrawer);

  const observerHandle = initTocObserver(headingEntries, entryById, scrollOffset, setActive);
  const scrollHandle = initTocScroll(nav, progress, scrollOffset);

  if (window.location.hash) {
    try {
      const hashId = window.location.hash.slice(1);
      const hashLink = nav.querySelector<HTMLElement>(`[${TOC_ATTRS.tocId}="${hashId}"]`);
      if (hashLink) autoExpandAncestors(hashLink);
    } catch {
      // Ignore malformed hash selectors.
    }
  }

  return () => {
    observerHandle.cleanup();
    scrollHandle.cleanup();
    drawer.cleanup();
    cleanupExpandButtons();
    nav.removeEventListener("click", onNavLinkCloseDrawer);
    setPanelSemantics(false);
  };
}
