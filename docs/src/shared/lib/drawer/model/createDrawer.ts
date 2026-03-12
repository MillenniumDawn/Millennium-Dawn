import { bindDrawerEvents, closeDrawer, finishClose, openDrawer } from "../lib/runtime";
import { setToggleAttrs } from "../lib/dom";
import type { DrawerConfig, DrawerHandle, DrawerRuntime, DrawerState } from "./types";

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