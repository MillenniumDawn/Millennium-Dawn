type Cleanup = () => void;

const FOCUSABLE = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

export interface DrawerConfig {
  container: HTMLElement;
  panel: HTMLElement;
  toggle: HTMLElement;
  closeBtn?: HTMLElement | null;
  backdrop?: HTMLElement | null;
  desktopMQ: MediaQueryList;
  animMs: number;
  bodyLockClass: string;
  openLabels: { expanded: string; ariaLabel: string };
  closedLabels: { expanded: string; ariaLabel: string };
  lockScroll?: boolean;
  inertSelectors?: string[];
  onBeforeOpen?: () => void;
  onOpen?: () => void;
  onClose?: () => void;
  onAfterClose?: () => void;
}

export interface DrawerHandle {
  open(): void;
  close(restoreFocus?: boolean): void;
  toggle(): void;
  isOpen(): boolean;
  cleanup: Cleanup;
}

interface DrawerState {
  drawerOpen: boolean;
  lastFocused: Element | null;
  savedScrollY: number;
  closeTimer: number | null;
}

function setToggleAttrs(
  toggle: HTMLElement,
  open: boolean,
  openLabels: DrawerConfig["openLabels"],
  closedLabels: DrawerConfig["closedLabels"],
): void {
  const labels = open ? openLabels : closedLabels;
  toggle.setAttribute("aria-expanded", labels.expanded);
  toggle.setAttribute("aria-label", labels.ariaLabel);
}

function setPageInert(inertSelectors: string[], inert: boolean): void {
  inertSelectors.forEach((selector) => {
    const element =
      selector.startsWith("#")
        ? document.getElementById(selector.slice(1))
        : document.querySelector<HTMLElement>(selector);

    if (!element) return;

    if (inert) {
      element.setAttribute("inert", "");
      element.setAttribute("aria-hidden", "true");
      return;
    }

    element.removeAttribute("inert");
    element.removeAttribute("aria-hidden");
  });
}

function clearCloseTimer(state: DrawerState): void {
  if (state.closeTimer === null) return;
  window.clearTimeout(state.closeTimer);
  state.closeTimer = null;
}

function getFocusableEls(panel: HTMLElement): HTMLElement[] {
  return Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE)).filter((element) => element.offsetParent !== null);
}

function trapFocus(panel: HTMLElement, drawerOpen: boolean, event: KeyboardEvent): void {
  if (!drawerOpen || event.key !== "Tab") return;

  const focusables = getFocusableEls(panel);
  if (!focusables.length) return;

  const first = focusables[0];
  const last = focusables[focusables.length - 1];

  if (event.shiftKey) {
    if (document.activeElement === first) {
      event.preventDefault();
      last.focus();
    }
    return;
  }

  if (document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}

function syncToggleAndPageState(
  toggle: HTMLElement,
  bodyLockClass: string,
  openLabels: DrawerConfig["openLabels"],
  closedLabels: DrawerConfig["closedLabels"],
  inertSelectors: string[],
  open: boolean,
): void {
  if (open) {
    document.body.classList.add(bodyLockClass);
  } else {
    document.body.classList.remove(bodyLockClass);
  }

  setToggleAttrs(toggle, open, openLabels, closedLabels);
  setPageInert(inertSelectors, open);
}

function syncBodyScrollLock(state: DrawerState, lockScroll: boolean, open: boolean): void {
  if (!lockScroll) return;

  if (open) {
    state.savedScrollY = window.scrollY || window.pageYOffset;
    document.body.style.top = `-${state.savedScrollY}px`;
    return;
  }

  document.body.style.top = "";
  window.scrollTo(0, state.savedScrollY);
}

function focusDrawerEntry(panel: HTMLElement, closeBtn?: HTMLElement | null): void {
  window.setTimeout(() => {
    if (closeBtn instanceof HTMLElement) {
      closeBtn.focus();
      return;
    }

    const focusables = getFocusableEls(panel);
    if (focusables.length) focusables[0].focus();
  }, 40);
}

function registerMediaQueryListener(mediaQuery: MediaQueryList, listener: () => void): Cleanup {
  if (typeof mediaQuery.addEventListener === "function") {
    mediaQuery.addEventListener("change", listener);
    return () => {
      mediaQuery.removeEventListener("change", listener);
    };
  }

  return () => {};
}

export function createDrawer(config: DrawerConfig): DrawerHandle {
  const {
    container,
    panel,
    toggle,
    closeBtn,
    backdrop,
    desktopMQ,
    animMs,
    bodyLockClass,
    openLabels,
    closedLabels,
    lockScroll = false,
    inertSelectors = [],
    onBeforeOpen,
    onOpen,
    onClose,
    onAfterClose,
  } = config;

  const state: DrawerState = {
    drawerOpen: false,
    lastFocused: null,
    savedScrollY: 0,
    closeTimer: null,
  };

  const finishClose = () => {
    container.classList.remove("is-closing");
    clearCloseTimer(state);
    onAfterClose?.();
  };

  const open = () => {
    clearCloseTimer(state);

    onBeforeOpen?.();
    state.lastFocused = document.activeElement;
    state.drawerOpen = true;

    syncBodyScrollLock(state, lockScroll, true);

    container.classList.add("is-open");
    syncToggleAndPageState(toggle, bodyLockClass, openLabels, closedLabels, inertSelectors, true);
    onOpen?.();
    focusDrawerEntry(panel, closeBtn);
  };

  const close = (restoreFocus = true) => {
    state.drawerOpen = false;

    container.classList.add("is-closing");
    container.classList.remove("is-open");
    syncToggleAndPageState(toggle, bodyLockClass, openLabels, closedLabels, inertSelectors, false);
    onClose?.();

    syncBodyScrollLock(state, lockScroll, false);

    clearCloseTimer(state);
    state.closeTimer = window.setTimeout(finishClose, animMs);

    if (restoreFocus && state.lastFocused instanceof HTMLElement) {
      state.lastFocused.focus();
    }
  };

  const onToggleClick = () => {
    if (state.drawerOpen) {
      close();
    } else {
      open();
    }
  };

  const onCloseClick = () => {
    close();
  };

  const onBackdropClick = () => {
    if (state.drawerOpen) close();
  };

  const onKeydown = (event: KeyboardEvent) => {
    if (event.key === "Escape" && state.drawerOpen) close();
    trapFocus(panel, state.drawerOpen, event);
  };

  const onBreakpoint = () => {
    if (desktopMQ.matches && state.drawerOpen) close(false);
  };

  toggle.addEventListener("click", onToggleClick);
  if (closeBtn) closeBtn.addEventListener("click", onCloseClick);
  if (backdrop) backdrop.addEventListener("click", onBackdropClick);
  document.addEventListener("keydown", onKeydown);
  const removeBreakpointListener = registerMediaQueryListener(desktopMQ, onBreakpoint);

  const cleanup = () => {
    toggle.removeEventListener("click", onToggleClick);
    if (closeBtn) closeBtn.removeEventListener("click", onCloseClick);
    if (backdrop) backdrop.removeEventListener("click", onBackdropClick);
    document.removeEventListener("keydown", onKeydown);
    removeBreakpointListener();

    if (state.drawerOpen) {
      close(false);
    } else {
      finishClose();
    }

    container.classList.remove("is-open", "is-closing");
    setToggleAttrs(toggle, false, openLabels, closedLabels);
  };

  return { open, close, toggle: onToggleClick, isOpen: () => state.drawerOpen, cleanup };
}
