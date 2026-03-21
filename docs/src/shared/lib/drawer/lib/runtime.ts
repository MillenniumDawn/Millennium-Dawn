import { focusDrawerEntry, setPageInert, setToggleAttrs, trapFocus } from "./dom";
import type { Cleanup, DrawerRuntime, DrawerState } from "../model/types";

export function clearCloseTimer(state: DrawerState): void {
  if (state.closeTimer === null) return;
  window.clearTimeout(state.closeTimer);
  state.closeTimer = null;
}

export function registerMediaQueryListener(mediaQuery: MediaQueryList, listener: () => void): Cleanup {
  if (typeof mediaQuery.addEventListener === "function") {
    mediaQuery.addEventListener("change", listener);
    return () => {
      mediaQuery.removeEventListener("change", listener);
    };
  }

  return () => {};
}

export function syncToggleAndPageState(
  toggle: HTMLElement,
  bodyLockClass: string,
  openLabels: DrawerRuntime["openLabels"],
  closedLabels: DrawerRuntime["closedLabels"],
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

export function syncBodyScrollLock(state: DrawerState, lockScroll: boolean, open: boolean): void {
  if (!lockScroll) return;

  if (open) {
    state.savedScrollY = window.scrollY || window.pageYOffset;
    document.body.style.top = `-${state.savedScrollY}px`;
    return;
  }

  document.body.style.top = "";
  const root = document.documentElement;
  const prevBehavior = root.style.scrollBehavior;
  root.style.scrollBehavior = "auto";
  window.scrollTo({ top: state.savedScrollY, left: 0, behavior: "auto" });
  window.setTimeout(() => {
    root.style.scrollBehavior = prevBehavior;
  }, 0);
}

export function finishClose(runtime: DrawerRuntime, state: DrawerState): void {
  runtime.container.classList.remove("is-closing");
  clearCloseTimer(state);
  runtime.onAfterClose?.();
}

export function openDrawer(runtime: DrawerRuntime, state: DrawerState): void {
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

export function closeDrawer(runtime: DrawerRuntime, state: DrawerState, restoreFocus = true): void {
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

export function bindDrawerEvents(
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
