import type { DrawerConfig } from "../model/types";

const FOCUSABLE = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function setToggleAttrs(
  toggle: HTMLElement,
  open: boolean,
  openLabels: DrawerConfig["openLabels"],
  closedLabels: DrawerConfig["closedLabels"],
): void {
  const labels = open ? openLabels : closedLabels;
  toggle.setAttribute("aria-expanded", labels.expanded);
  toggle.setAttribute("aria-label", labels.ariaLabel);
}

export function setPageInert(inertSelectors: string[], inert: boolean): void {
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

export function getFocusableEls(panel: HTMLElement): HTMLElement[] {
  return Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE)).filter((element) => element.offsetParent !== null);
}

export function trapFocus(panel: HTMLElement, drawerOpen: boolean, event: KeyboardEvent): void {
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

export function focusDrawerEntry(panel: HTMLElement, closeBtn?: HTMLElement | null): void {
  window.setTimeout(() => {
    if (closeBtn instanceof HTMLElement) {
      closeBtn.focus({ preventScroll: true });
      return;
    }

    const focusables = getFocusableEls(panel);
    if (focusables.length) focusables[0].focus({ preventScroll: true });
  }, 40);
}