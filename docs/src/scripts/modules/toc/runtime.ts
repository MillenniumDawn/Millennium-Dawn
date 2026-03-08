import { bindExpandButtons, buildTree, ensureHeadingIds, renderNav, toggleSublist } from "./render";
import { readCssMsVar, readCssPxVar, readCssStringVar } from "../tokens";
import { createDrawer } from "../shared/drawer";
import { initTocObserver } from "./observer";
import { initTocScroll } from "./scroll";
import type { TocEntry } from "./types";

type Cleanup = () => void;

const NOOP: Cleanup = () => {};

export function initToc(): Cleanup {
  const sidebar = document.getElementById("toc-sidebar");

  if (document.body.dataset.toc === "off") {
    document.body.classList.remove("has-toc");
    if (sidebar) sidebar.hidden = true;
    return NOOP;
  }

  const scrollOffset = readCssPxVar("--toc-scroll-offset", 120);
  const drawerAnimMs = readCssMsVar("--duration-toc-drawer", 280);
  const wideMin = readCssStringVar("--bp-wide-min", "1100px");

  const panel = document.getElementById("toc-panel");
  const nav = document.getElementById("toc-nav");
  const toggle = document.getElementById("toc-toggle");
  const closeBtn = document.getElementById("toc-close");
  const backdrop = document.getElementById("toc-backdrop");
  const progress = document.getElementById("toc-progress");
  if (!sidebar || !panel || !nav || !toggle) return NOOP;

  const content = document.querySelector<HTMLElement>(".main-content");
  if (!content) return NOOP;

  let allLinks = Array.from(nav.querySelectorAll<HTMLAnchorElement>(".toc-sidebar__link"));
  if (!allLinks.length) {
    const headings = Array.from(content.querySelectorAll<HTMLHeadingElement>("h2, h3, h4"));
    if (!headings.length) {
      document.body.classList.remove("has-toc");
      sidebar.hidden = true;
      return NOOP;
    }

    ensureHeadingIds(headings);
    renderNav(nav, buildTree(headings));
    bindExpandButtons(nav);
    allLinks = Array.from(nav.querySelectorAll<HTMLAnchorElement>(".toc-sidebar__link"));
  } else {
    bindExpandButtons(nav);
  }

  sidebar.hidden = false;
  document.body.classList.add("has-toc");

  const headingEntries: TocEntry[] = [];
  const entryById: Record<string, TocEntry> = {};
  let currentActive: TocEntry | null = null;

  allLinks.forEach((link) => {
    const id = link.getAttribute("data-toc-id");
    if (!id) return;

    const headingEl = document.getElementById(id);
    if (!(headingEl instanceof HTMLElement)) return;

    const entry: TocEntry = { el: headingEl, link };
    headingEntries.push(entry);
    entryById[id] = entry;
  });

  if (!headingEntries.length) {
    document.body.classList.remove("has-toc");
    sidebar.hidden = true;
    return NOOP;
  }

  // --- Active-heading helpers ---

  const autoExpandAncestors = (link: HTMLElement) => {
    let node = link.parentElement;
    while (node && node !== nav) {
      if (node.classList.contains("toc-sidebar__sublist") && !node.classList.contains("is-expanded")) {
        const idx = node.getAttribute("data-toc-sublist");
        if (!idx) {
          node = node.parentElement;
          continue;
        }

        const button = nav.querySelector<HTMLElement>(`[data-toc-expand="${idx}"]`);
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
      currentActive.link.classList.remove("is-active");
      currentActive.link.removeAttribute("aria-current");
    }

    currentActive = nextActive;

    if (currentActive) {
      currentActive.link.classList.add("is-active");
      currentActive.link.setAttribute("aria-current", "location");
      autoExpandAncestors(currentActive.link);
      scrollTocIntoView(currentActive.link);
    }
  };

  // --- Panel semantics (dialog on mobile, region on desktop) ---

  const setPanelSemantics = (dialogMode: boolean) => {
    panel.setAttribute("role", dialogMode ? "dialog" : "region");
    if (dialogMode) {
      panel.setAttribute("aria-modal", "true");
    } else {
      panel.removeAttribute("aria-modal");
    }
  };

  setPanelSemantics(false);

  // --- Drawer (mobile slide-out) ---

  const drawer = createDrawer({
    container: sidebar,
    panel,
    toggle,
    closeBtn,
    backdrop,
    desktopMQ: window.matchMedia(`(min-width: ${wideMin})`),
    animMs: drawerAnimMs,
    bodyLockClass: "toc-lock",
    openLabels: { expanded: "true", ariaLabel: "Close table of contents" },
    closedLabels: { expanded: "false", ariaLabel: "Open table of contents" },
    lockScroll: true,
    inertSelectors: ["#main-content", ".site-header", ".site-footer"],
    onOpen: () => setPanelSemantics(true),
    onClose: () => setPanelSemantics(false),
  });

  // Close drawer when a ToC link is clicked on mobile
  const onNavLinkCloseDrawer = (event: MouseEvent) => {
    if (event.target instanceof Element && event.target.closest(".toc-sidebar__link") && drawer.isOpen()) {
      drawer.close(false);
    }
  };
  nav.addEventListener("click", onNavLinkCloseDrawer);

  // --- Observer (active heading tracking) ---

  const observerHandle = initTocObserver(headingEntries, entryById, scrollOffset, setActive);

  // --- Scroll (smooth-scroll + progress bar) ---

  const scrollHandle = initTocScroll(nav, progress, scrollOffset);

  // --- Hash-expand on load ---

  if (window.location.hash) {
    try {
      const hashId = window.location.hash.slice(1);
      const hashLink = nav.querySelector<HTMLElement>(`[data-toc-id="${hashId}"]`);
      if (hashLink) autoExpandAncestors(hashLink);
    } catch {
      // Ignore malformed hash selectors.
    }
  }

  // --- Cleanup ---

  return () => {
    observerHandle.cleanup();
    scrollHandle.cleanup();
    drawer.cleanup();
    nav.removeEventListener("click", onNavLinkCloseDrawer);
    setPanelSemantics(false);
  };
}
