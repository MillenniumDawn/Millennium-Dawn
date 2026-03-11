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

interface DrawerRuntime {
  container: HTMLElement;
  panel: HTMLElement;
  toggle: HTMLElement;
  closeBtn?: HTMLElement | null;
  backdrop?: HTMLElement | null;
  desktopMQ: MediaQueryList;
  animMs: number;
  bodyLockClass: string;
  openLabels: DrawerConfig["openLabels"];
  closedLabels: DrawerConfig["closedLabels"];
  lockScroll: boolean;
  inertSelectors: string[];
  onBeforeOpen?: () => void;
  onOpen?: () => void;
  onClose?: () => void;
  onAfterClose?: () => void;
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
      closeBtn.focus({ preventScroll: true });
      return;
    }

    const focusables = getFocusableEls(panel);
    if (focusables.length) focusables[0].focus({ preventScroll: true });
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

function finishClose(runtime: DrawerRuntime, state: DrawerState): void {
  runtime.container.classList.remove("is-closing");
  clearCloseTimer(state);
  runtime.onAfterClose?.();
}

function openDrawer(runtime: DrawerRuntime, state: DrawerState): void {
  clearCloseTimer(state);

  runtime.onBeforeOpen?.();
  state.lastFocused = document.activeElement;
  state.drawerOpen = true;

  syncBodyScrollLock(state, runtime.lockScroll, true);

  runtime.container.classList.add("is-open");
  syncToggleAndPageState(
    runtime.toggle,
    runtime.bodyLockClass,
    runtime.openLabels,
    runtime.closedLabels,
    runtime.inertSelectors,
    true,
  );
  runtime.onOpen?.();
  focusDrawerEntry(runtime.panel, runtime.closeBtn);
}

function closeDrawer(runtime: DrawerRuntime, state: DrawerState, restoreFocus = true): void {
  state.drawerOpen = false;

  runtime.container.classList.add("is-closing");
  runtime.container.classList.remove("is-open");
  syncToggleAndPageState(
    runtime.toggle,
    runtime.bodyLockClass,
    runtime.openLabels,
    runtime.closedLabels,
    runtime.inertSelectors,
    false,
  );
  runtime.onClose?.();

  syncBodyScrollLock(state, runtime.lockScroll, false);

  clearCloseTimer(state);
  state.closeTimer = window.setTimeout(() => finishClose(runtime, state), runtime.animMs);

  if (restoreFocus && state.lastFocused instanceof HTMLElement) {
    state.lastFocused.focus();
  }
}

function bindDrawerEvents(
  runtime: DrawerRuntime,
  state: DrawerState,
  open: () => void,
  close: (restoreFocus?: boolean) => void,
): Cleanup {
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
    trapFocus(runtime.panel, state.drawerOpen, event);
  };

  const onBreakpoint = () => {
    if (runtime.desktopMQ.matches && state.drawerOpen) close(false);
  };

  runtime.toggle.addEventListener("click", onToggleClick);
  if (runtime.closeBtn) runtime.closeBtn.addEventListener("click", onCloseClick);
  if (runtime.backdrop) runtime.backdrop.addEventListener("click", onBackdropClick);
  document.addEventListener("keydown", onKeydown);
  const removeBreakpointListener = registerMediaQueryListener(runtime.desktopMQ, onBreakpoint);

  return () => {
    runtime.toggle.removeEventListener("click", onToggleClick);
    if (runtime.closeBtn) runtime.closeBtn.removeEventListener("click", onCloseClick);
    if (runtime.backdrop) runtime.backdrop.removeEventListener("click", onBackdropClick);
    document.removeEventListener("keydown", onKeydown);
    removeBreakpointListener();
  };
}

export function createDrawer(config: DrawerConfig): DrawerHandle {
  const runtime: DrawerRuntime = {
    ...config,
    lockScroll: config.lockScroll ?? false,
    inertSelectors: config.inertSelectors ?? [],
  };
  const state: DrawerState = {
    drawerOpen: false,
    lastFocused: null,
    savedScrollY: 0,
    closeTimer: null,
  };
  const open = () => {
    openDrawer(runtime, state);
  };
  const close = (restoreFocus = true) => {
    closeDrawer(runtime, state, restoreFocus);
  };
  const removeListeners = bindDrawerEvents(runtime, state, open, close);

  const cleanup = () => {
    removeListeners();

    if (state.drawerOpen) {
      close(false);
    } else {
      finishClose(runtime, state);
    }

    runtime.container.classList.remove("is-open", "is-closing");
    setToggleAttrs(runtime.toggle, false, runtime.openLabels, runtime.closedLabels);
  };

  return { open, close, toggle: () => (state.drawerOpen ? close() : open()), isOpen: () => state.drawerOpen, cleanup };
}
