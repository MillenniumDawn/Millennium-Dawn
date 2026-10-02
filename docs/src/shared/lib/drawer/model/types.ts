export type Cleanup = () => void;

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

export interface DrawerState {
  drawerOpen: boolean;
  lastFocused: Element | null;
  savedScrollY: number;
  closeTimer: number | null;
}

export interface DrawerRuntime {
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
