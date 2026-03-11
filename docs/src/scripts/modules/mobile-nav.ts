import { createDrawer } from "@/shared/lib/drawer";
import { readCssMsVar, readCssStringVar } from "@/shared/lib/tokens";

type Cleanup = () => void;

const NOOP: Cleanup = () => {};

function dispatchHeaderState(header: HTMLElement): void {
  header.dispatchEvent(new CustomEvent("navstatechange"));
}

function setNavHidden(nav: HTMLElement, hidden: boolean): void {
  if (hidden) {
    nav.setAttribute("hidden", "");
    nav.setAttribute("aria-hidden", "true");
    nav.setAttribute("inert", "");
  } else {
    nav.removeAttribute("hidden");
    nav.removeAttribute("aria-hidden");
    nav.removeAttribute("inert");
  }
}

export function initMobileNavigation(): Cleanup {
  const toggle = document.querySelector<HTMLButtonElement>(".nav-toggle");
  const nav = document.getElementById("main-nav");
  const header = document.querySelector<HTMLElement>(".site-header");
  if (!toggle || !nav || !header) return NOOP;

  const tabletMin = readCssStringVar("--bp-tablet-min", "769px");
  const closeAnimMs = readCssMsVar("--duration-nav-close", 320);
  const desktopMQ = window.matchMedia(`(min-width: ${tabletMin})`);

  const drawer = createDrawer({
    container: nav,
    panel: nav,
    toggle,
    desktopMQ,
    animMs: closeAnimMs,
    bodyLockClass: "nav-lock",
    openLabels: { expanded: "true", ariaLabel: "Close navigation menu" },
    closedLabels: { expanded: "false", ariaLabel: "Open navigation menu" },
    onBeforeOpen: () => setNavHidden(nav, false),
    onOpen: () => {
      header.classList.add("nav-is-open");
      dispatchHeaderState(header);
    },
    onClose: () => {
      header.classList.remove("nav-is-open");
      dispatchHeaderState(header);
    },
    onAfterClose: () => {
      if (!desktopMQ.matches) {
        setNavHidden(nav, true);
      }
    },
  });

  const syncByViewport = () => {
    if (desktopMQ.matches) {
      setNavHidden(nav, false);
      header.classList.remove("nav-is-open");
      document.body.classList.remove("nav-lock");
      dispatchHeaderState(header);
      return;
    }

    if (!drawer.isOpen()) {
      setNavHidden(nav, true);
      header.classList.remove("nav-is-open");
      document.body.classList.remove("nav-lock");
      dispatchHeaderState(header);
    }
  };

  const onDocumentClick = (event: MouseEvent) => {
    if (!(event.target instanceof Node)) return;
    if (drawer.isOpen() && !nav.contains(event.target) && !toggle.contains(event.target)) {
      drawer.close(false);
    }
  };

  const onNavClick = (event: MouseEvent) => {
    if (event.target instanceof Element && event.target.closest("a") && drawer.isOpen()) {
      drawer.close(false);
    }
  };

  const onMediaChange = () => {
    syncByViewport();
  };

  document.addEventListener("click", onDocumentClick);
  nav.addEventListener("click", onNavClick);

  if (typeof desktopMQ.addEventListener === "function") {
    desktopMQ.addEventListener("change", onMediaChange);
  }

  syncByViewport();

  return () => {
    document.removeEventListener("click", onDocumentClick);
    nav.removeEventListener("click", onNavClick);
    if (typeof desktopMQ.removeEventListener === "function") {
      desktopMQ.removeEventListener("change", onMediaChange);
    }

    drawer.cleanup();
    header.classList.remove("nav-is-open");
    document.body.classList.remove("nav-lock");
    setNavHidden(nav, desktopMQ.matches ? false : true);
    dispatchHeaderState(header);
  };
}
