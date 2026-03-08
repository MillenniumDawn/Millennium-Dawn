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
  onOpen?: () => void;
  onClose?: () => void;
}

export interface DrawerHandle {
  open(): void;
  close(restoreFocus?: boolean): void;
  toggle(): void;
  isOpen(): boolean;
  cleanup: Cleanup;
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
    onOpen,
    onClose,
  } = config;

  let drawerOpen = false;
  let lastFocused: Element | null = null;
  let savedScrollY = 0;

  const getFocusableEls = (): HTMLElement[] =>
    Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE)).filter((el) => el.offsetParent !== null);

  const setToggleAttrs = (open: boolean) => {
    const labels = open ? openLabels : closedLabels;
    toggle.setAttribute("aria-expanded", labels.expanded);
    toggle.setAttribute("aria-label", labels.ariaLabel);
  };

  const setPageInert = (inert: boolean) => {
    inertSelectors.forEach((selector) => {
      const el =
        selector.startsWith("#")
          ? document.getElementById(selector.slice(1))
          : document.querySelector<HTMLElement>(selector);
      if (!el) return;
      if (inert) {
        el.setAttribute("inert", "");
        el.setAttribute("aria-hidden", "true");
      } else {
        el.removeAttribute("inert");
        el.removeAttribute("aria-hidden");
      }
    });
  };

  const open = () => {
    lastFocused = document.activeElement;
    drawerOpen = true;

    if (lockScroll) {
      savedScrollY = window.scrollY || window.pageYOffset;
      document.body.style.top = `-${savedScrollY}px`;
    }

    container.classList.add("is-open");
    document.body.classList.add(bodyLockClass);
    setToggleAttrs(true);
    setPageInert(true);
    onOpen?.();

    window.setTimeout(() => {
      if (closeBtn instanceof HTMLElement) {
        closeBtn.focus();
      } else {
        const focusables = getFocusableEls();
        if (focusables.length) focusables[0].focus();
      }
    }, 40);
  };

  const close = (restoreFocus = true) => {
    drawerOpen = false;

    container.classList.add("is-closing");
    container.classList.remove("is-open");
    document.body.classList.remove(bodyLockClass);
    setToggleAttrs(false);
    setPageInert(false);
    onClose?.();

    if (lockScroll) {
      document.body.style.top = "";
      window.scrollTo(0, savedScrollY);
    }

    window.setTimeout(() => {
      container.classList.remove("is-closing");
    }, animMs);

    if (restoreFocus && lastFocused instanceof HTMLElement) {
      lastFocused.focus();
    }
  };

  const trapFocus = (event: KeyboardEvent) => {
    if (!drawerOpen || event.key !== "Tab") return;
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

  const onToggleClick = () => {
    if (drawerOpen) { close(); } else { open(); }
  };

  const onCloseClick = () => {
    close();
  };

  const onBackdropClick = () => {
    if (drawerOpen) close();
  };

  const onKeydown = (event: KeyboardEvent) => {
    if (event.key === "Escape" && drawerOpen) close();
    trapFocus(event);
  };

  const onBreakpoint = () => {
    if (desktopMQ.matches && drawerOpen) close(false);
  };

  toggle.addEventListener("click", onToggleClick);
  if (closeBtn) closeBtn.addEventListener("click", onCloseClick);
  if (backdrop) backdrop.addEventListener("click", onBackdropClick);
  document.addEventListener("keydown", onKeydown);

  if (typeof desktopMQ.addEventListener === "function") {
    desktopMQ.addEventListener("change", onBreakpoint);
  }

  const cleanup = () => {
    toggle.removeEventListener("click", onToggleClick);
    if (closeBtn) closeBtn.removeEventListener("click", onCloseClick);
    if (backdrop) backdrop.removeEventListener("click", onBackdropClick);
    document.removeEventListener("keydown", onKeydown);

    if (typeof desktopMQ.removeEventListener === "function") {
      desktopMQ.removeEventListener("change", onBreakpoint);
    }

    if (drawerOpen) {
      drawerOpen = false;
      document.body.classList.remove(bodyLockClass);
      if (lockScroll) document.body.style.top = "";
      setPageInert(false);
    }

    container.classList.remove("is-open", "is-closing");
    setToggleAttrs(false);
  };

  return { open, close, toggle: onToggleClick, isOpen: () => drawerOpen, cleanup };
}
