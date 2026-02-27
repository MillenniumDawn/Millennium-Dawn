import { readCssMsVar, readCssStringVar } from "./tokens";

type Cleanup = () => void;

const NOOP: Cleanup = () => {};

export function initHeaderHeightSync(): Cleanup {
  const root = document.documentElement;
  const header = document.querySelector<HTMLElement>(".site-header");
  if (!root || !header) return NOOP;

  const update = () => {
    const height = Math.ceil(header.getBoundingClientRect().height);
    if (height > 0) root.style.setProperty("--header-height", `${height}px`);
  };

  update();
  window.addEventListener("load", update);
  window.addEventListener("resize", update);
  header.addEventListener("navstatechange", update);

  let observer: ResizeObserver | null = null;
  if (typeof ResizeObserver !== "undefined") {
    observer = new ResizeObserver(update);
    observer.observe(header);
  }

  return () => {
    window.removeEventListener("load", update);
    window.removeEventListener("resize", update);
    header.removeEventListener("navstatechange", update);
    observer?.disconnect();
  };
}

export function initMobileNavigation(): Cleanup {
  const toggle = document.querySelector<HTMLButtonElement>(".nav-toggle");
  const nav = document.getElementById("main-nav");
  const header = document.querySelector<HTMLElement>(".site-header");
  if (!toggle || !nav || !header) return NOOP;

  const tabletMin = readCssStringVar("--bp-tablet-min", "769px");
  const desktopMQ = window.matchMedia(`(min-width: ${tabletMin})`);
  const focusableSelector = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';
  const closeAnimMs = readCssMsVar("--duration-nav-close", 320);
  let closeTimer: number | null = null;

  const isDesktop = () => desktopMQ.matches;
  const isOpen = () => nav.classList.contains("is-open");

  const dispatchHeaderState = () => {
    header.dispatchEvent(new CustomEvent("navstatechange"));
  };

  const setToggleState = (open: boolean) => {
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    toggle.setAttribute("aria-label", open ? "Close navigation menu" : "Open navigation menu");
  };

  const setNavHidden = (hidden: boolean) => {
    if (hidden) {
      nav.setAttribute("hidden", "");
      nav.setAttribute("aria-hidden", "true");
      nav.setAttribute("inert", "");
    } else {
      nav.removeAttribute("hidden");
      nav.removeAttribute("aria-hidden");
      nav.removeAttribute("inert");
    }
  };

  const finishClose = () => {
    nav.classList.remove("is-closing");
    if (!isDesktop() && !isOpen()) setNavHidden(true);
  };

  const getFocusableNavEls = (): HTMLElement[] =>
    Array.from(nav.querySelectorAll<HTMLElement>(focusableSelector)).filter((el) => el.offsetParent !== null);

  const openNav = () => {
    if (isDesktop()) return;

    if (closeTimer !== null) {
      window.clearTimeout(closeTimer);
      closeTimer = null;
    }

    nav.classList.remove("is-closing");
    setNavHidden(false);

    requestAnimationFrame(() => {
      nav.classList.add("is-open");
    });

    header.classList.add("nav-is-open");
    document.body.classList.add("nav-lock");
    setToggleState(true);
    dispatchHeaderState();

    window.setTimeout(() => {
      const focusables = getFocusableNavEls();
      if (focusables.length) focusables[0].focus();
    }, 30);
  };

  const closeNav = (restoreFocus: boolean) => {
    nav.classList.remove("is-open");
    nav.classList.add("is-closing");
    header.classList.remove("nav-is-open");
    document.body.classList.remove("nav-lock");
    setToggleState(false);
    dispatchHeaderState();

    if (closeTimer !== null) window.clearTimeout(closeTimer);
    closeTimer = window.setTimeout(finishClose, closeAnimMs);

    if (restoreFocus) toggle.focus();
  };

  const trapFocus = (event: KeyboardEvent) => {
    if (isDesktop() || !isOpen() || event.key !== "Tab") return;

    const focusables = getFocusableNavEls();
    if (!focusables.length) return;

    const first = focusables[0];
    const last = focusables[focusables.length - 1];

    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  };

  const syncByViewport = () => {
    if (closeTimer !== null) {
      window.clearTimeout(closeTimer);
      closeTimer = null;
    }

    if (isDesktop()) {
      nav.classList.remove("is-open", "is-closing");
      header.classList.remove("nav-is-open");
      document.body.classList.remove("nav-lock");
      setNavHidden(false);
      setToggleState(false);
      dispatchHeaderState();
      return;
    }

    if (!isOpen()) {
      nav.classList.remove("is-closing");
      setNavHidden(true);
      setToggleState(false);
      header.classList.remove("nav-is-open");
      document.body.classList.remove("nav-lock");
      dispatchHeaderState();
    }
  };

  const onToggleClick = () => {
    isOpen() ? closeNav(false) : openNav();
  };

  const onDocumentKeydown = (event: KeyboardEvent) => {
    if (event.key === "Escape" && isOpen()) closeNav(true);
    trapFocus(event);
  };

  const onDocumentClick = (event: MouseEvent) => {
    if (!(event.target instanceof Node)) return;
    if (isOpen() && !nav.contains(event.target) && !toggle.contains(event.target)) {
      closeNav(false);
    }
  };

  const onNavClick = (event: MouseEvent) => {
    if (event.target instanceof Element && event.target.closest("a") && isOpen()) closeNav(false);
  };

  const onNavTransitionEnd = (event: TransitionEvent) => {
    if (event.propertyName === "max-height" && !isOpen() && !isDesktop()) {
      finishClose();
    }
  };

  const onMediaChange = () => {
    syncByViewport();
  };

  toggle.addEventListener("click", onToggleClick);
  document.addEventListener("keydown", onDocumentKeydown);
  document.addEventListener("click", onDocumentClick);
  nav.addEventListener("click", onNavClick);
  nav.addEventListener("transitionend", onNavTransitionEnd);

  if (typeof desktopMQ.addEventListener === "function") {
    desktopMQ.addEventListener("change", onMediaChange);
  }

  syncByViewport();

  return () => {
    if (closeTimer !== null) {
      window.clearTimeout(closeTimer);
      closeTimer = null;
    }
    toggle.removeEventListener("click", onToggleClick);
    document.removeEventListener("keydown", onDocumentKeydown);
    document.removeEventListener("click", onDocumentClick);
    nav.removeEventListener("click", onNavClick);
    nav.removeEventListener("transitionend", onNavTransitionEnd);
    if (typeof desktopMQ.removeEventListener === "function") {
      desktopMQ.removeEventListener("change", onMediaChange);
    }

    nav.classList.remove("is-open", "is-closing");
    header.classList.remove("nav-is-open");
    document.body.classList.remove("nav-lock");
    setToggleState(false);
    setNavHidden(desktopMQ.matches ? false : true);
  };
}
