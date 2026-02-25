import { bindExpandButtons, buildTree, ensureHeadingIds, renderNav, toggleSublist } from "./render";
import { readCssMsVar, readCssPxVar, readCssStringVar } from "../tokens";

type TocEntry = {
  el: HTMLElement;
  link: HTMLAnchorElement;
};

export function initToc(): void {
  const sidebar = document.getElementById("toc-sidebar");

  if (document.body.dataset.toc === "off") {
    document.body.classList.remove("has-toc");
    if (sidebar) sidebar.hidden = true;
    return;
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
  if (!sidebar || !panel || !nav) return;

  const content = document.querySelector<HTMLElement>(".main-content");
  if (!content) return;

  let allLinks = Array.from(nav.querySelectorAll<HTMLAnchorElement>(".toc-sidebar__link"));
  if (!allLinks.length) {
    const headings = Array.from(content.querySelectorAll<HTMLHeadingElement>("h2, h3, h4"));
    if (!headings.length) {
      document.body.classList.remove("has-toc");
      sidebar.hidden = true;
      return;
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
    return;
  }

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

  const updateProgress = () => {
    if (!progress) return;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const pct = docHeight > 0 ? Math.min(100, ((window.scrollY || 0) / docHeight) * 100) : 0;
    (progress as HTMLElement).style.width = `${pct}%`;
  };

  const findActiveFallback = (): TocEntry | null => {
    let active: TocEntry | null = null;
    for (let i = headingEntries.length - 1; i >= 0; i -= 1) {
      if (headingEntries[i].el.getBoundingClientRect().top <= scrollOffset) {
        active = headingEntries[i];
        break;
      }
    }
    return active || headingEntries[0] || null;
  };

  const visibleHeadings = new Map<string, number>();
  let observer: IntersectionObserver | null = null;

  const pickVisibleActive = (): TocEntry | null => {
    if (!visibleHeadings.size) {
      if ((window.scrollY || 0) < 32) return headingEntries[0] || null;
      return currentActive || findActiveFallback();
    }

    let bestEntry: TocEntry | null = null;
    let bestDistance = Number.POSITIVE_INFINITY;

    visibleHeadings.forEach((top, id) => {
      const entry = entryById[id];
      if (!entry) return;

      const distance = Math.abs(top - scrollOffset);
      if (distance < bestDistance) {
        bestDistance = distance;
        bestEntry = entry;
      }
    });

    return bestEntry || currentActive || findActiveFallback();
  };

  if (typeof IntersectionObserver !== "undefined") {
    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const target = entry.target as HTMLElement;
          if (entry.isIntersecting) {
            visibleHeadings.set(target.id, entry.boundingClientRect.top);
          } else {
            visibleHeadings.delete(target.id);
          }
        });
        setActive(pickVisibleActive());
      },
      {
        root: null,
        rootMargin: `-${scrollOffset}px 0px -55% 0px`,
        threshold: [0, 1],
      },
    );

    headingEntries.forEach((entry) => {
      observer?.observe(entry.el);
    });
    setActive(headingEntries[0]);
  } else {
    setActive(findActiveFallback());
  }

  let rafPending = false;
  const onScroll = () => {
    if (rafPending) return;
    rafPending = true;
    requestAnimationFrame(() => {
      rafPending = false;
      if (!observer) setActive(findActiveFallback());
      updateProgress();
    });
  };

  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", () => {
    if (!observer) setActive(findActiveFallback());
    updateProgress();
  });
  updateProgress();

  let isDrawerOpen = false;
  let lastFocused: Element | null = null;
  const desktopMQ = window.matchMedia(`(min-width: ${wideMin})`);
  const focusableSelector = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';
  let savedScrollY = 0;

  const getFocusableEls = (): HTMLElement[] =>
    Array.from(panel.querySelectorAll<HTMLElement>(focusableSelector)).filter((el) => el.offsetParent !== null);

  const setPageInert = (inert: boolean) => {
    const elements: Array<HTMLElement | null> = [
      document.getElementById("main-content"),
      document.querySelector<HTMLElement>(".site-header"),
      document.querySelector<HTMLElement>(".site-footer"),
    ];

    elements.forEach((element) => {
      if (!element) return;
      if (inert) {
        element.setAttribute("inert", "");
        element.setAttribute("aria-hidden", "true");
      } else {
        element.removeAttribute("inert");
        element.removeAttribute("aria-hidden");
      }
    });
  };

  const openDrawer = () => {
    if (!toggle) return;
    lastFocused = document.activeElement;
    isDrawerOpen = true;

    savedScrollY = window.scrollY || window.pageYOffset;
    sidebar.classList.add("is-open");
    toggle.setAttribute("aria-expanded", "true");
    toggle.setAttribute("aria-label", "Close table of contents");
    document.body.classList.add("toc-lock");
    document.body.style.top = `-${savedScrollY}px`;
    setPageInert(true);

    window.setTimeout(() => {
      if (closeBtn instanceof HTMLElement) {
        closeBtn.focus();
      } else {
        const focusables = getFocusableEls();
        if (focusables.length) focusables[0].focus();
      }
    }, 40);
  };

  const closeDrawer = (restoreFocus = true) => {
    if (!toggle) return;
    isDrawerOpen = false;

    sidebar.classList.add("is-closing");
    sidebar.classList.remove("is-open");
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "Open table of contents");
    document.body.classList.remove("toc-lock");
    document.body.style.top = "";
    window.scrollTo(0, savedScrollY);
    setPageInert(false);

    window.setTimeout(() => {
      sidebar.classList.remove("is-closing");
    }, drawerAnimMs);

    if (restoreFocus && lastFocused instanceof HTMLElement) {
      lastFocused.focus();
    }
  };

  const trapFocus = (event: KeyboardEvent) => {
    if (!isDrawerOpen || event.key !== "Tab") return;
    const focusables = getFocusableEls();
    if (!focusables.length) return;

    const first = focusables[0];
    const last = focusables[focusables.length - 1];

    if (event.shiftKey) {
      if (document.activeElement === first) {
        event.preventDefault();
        last.focus();
      }
    } else if (document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  };

  if (toggle) {
    toggle.addEventListener("click", () => {
      isDrawerOpen ? closeDrawer() : openDrawer();
    });
  }

  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      closeDrawer();
    });
  }

  if (backdrop) {
    backdrop.addEventListener("click", () => {
      if (isDrawerOpen) closeDrawer();
    });
  }

  nav.addEventListener("click", (event) => {
    if (event.target instanceof Element && event.target.closest(".toc-sidebar__link") && isDrawerOpen) {
      closeDrawer(false);
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && isDrawerOpen) closeDrawer();
  });
  document.addEventListener("keydown", trapFocus);

  const onBreakpoint = () => {
    if (desktopMQ.matches && isDrawerOpen) closeDrawer(false);
  };

  if (typeof desktopMQ.addEventListener === "function") {
    desktopMQ.addEventListener("change", onBreakpoint);
  }

  nav.addEventListener("click", (event) => {
    if (!(event.target instanceof Element)) return;
    const link = event.target.closest<HTMLAnchorElement>(".toc-sidebar__link");
    if (!link) return;

    event.preventDefault();

    const targetId = link.getAttribute("data-toc-id");
    if (!targetId) return;

    const target = document.getElementById(targetId);
    if (!(target instanceof HTMLElement)) return;

    const header = document.querySelector<HTMLElement>(".site-header");
    const offset = header ? header.offsetHeight + 16 : scrollOffset;
    const targetTop = target.getBoundingClientRect().top + window.pageYOffset - offset;
    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: targetTop, behavior: prefersReduced ? "auto" : "smooth" });

    if (history.replaceState) history.replaceState(null, "", `#${targetId}`);

    target.setAttribute("tabindex", "-1");
    target.focus({ preventScroll: true });
  });

  if (window.location.hash) {
    try {
      const hashId = window.location.hash.slice(1);
      const hashLink = nav.querySelector<HTMLElement>(`[data-toc-id="${hashId}"]`);
      if (hashLink) autoExpandAncestors(hashLink);
    } catch {
      // Ignore malformed hash selectors.
    }
  }
}
