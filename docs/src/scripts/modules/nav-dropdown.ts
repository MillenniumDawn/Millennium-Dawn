import { readCssStringVar } from "@/shared/lib/dom/tokens";

type Cleanup = () => void;

const NOOP: Cleanup = () => {};

interface Entry {
  group: HTMLElement;
  button: HTMLButtonElement;
}

/**
 * Desktop hover / keyboard / mobile-accordion behaviour for the top-bar
 * dropdown groups. `aria-expanded` on the toggle button is the single source
 * of truth; CSS reveals the panel from it (`peer-aria-expanded:` in Header.astro).
 */
export function initNavDropdowns(): Cleanup {
  const groups = Array.from(document.querySelectorAll<HTMLElement>(".nav-group"));
  if (groups.length === 0) return NOOP;

  const tabletMin = readCssStringVar("--bp-tablet-min", "769px");
  const desktopMQ = window.matchMedia(`(min-width: ${tabletMin})`);
  const hoverMQ = window.matchMedia("(hover: hover)");

  const entries: Entry[] = [];
  const cleanups: Cleanup[] = [];

  const isOpen = (entry: Entry) => entry.button.getAttribute("aria-expanded") === "true";
  const setOpen = (entry: Entry, open: boolean) => {
    entry.button.setAttribute("aria-expanded", open ? "true" : "false");
  };
  const closeAll = (except?: Entry) => {
    for (const entry of entries) {
      if (entry !== except) setOpen(entry, false);
    }
  };
  // Hover drives the menu only on a pointer-with-hover desktop; touch and
  // small screens fall back to click/tap toggling.
  const canHover = () => desktopMQ.matches && hoverMQ.matches;

  for (const group of groups) {
    const button = group.querySelector<HTMLButtonElement>(".nav-group-toggle");
    if (!button) continue;
    const entry: Entry = { group, button };
    entries.push(entry);

    const onClick = (event: MouseEvent) => {
      event.preventDefault();
      // A mouse click on a hover desktop would fight the hover state; ignore it.
      // Keyboard activation reports detail === 0, so Enter/Space still toggles.
      if (canHover() && event.detail !== 0) return;
      const open = !isOpen(entry);
      closeAll(entry);
      setOpen(entry, open);
    };

    const onPointerEnter = () => {
      if (!canHover()) return;
      closeAll(entry);
      setOpen(entry, true);
    };

    const onPointerLeave = () => {
      if (canHover()) setOpen(entry, false);
    };

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && isOpen(entry)) {
        setOpen(entry, false);
        button.focus();
      }
    };

    const onFocusOut = (event: FocusEvent) => {
      const next = event.relatedTarget;
      if (next instanceof Node && group.contains(next)) return;
      setOpen(entry, false);
    };

    button.addEventListener("click", onClick);
    group.addEventListener("pointerenter", onPointerEnter);
    group.addEventListener("pointerleave", onPointerLeave);
    group.addEventListener("keydown", onKeyDown);
    group.addEventListener("focusout", onFocusOut);

    cleanups.push(() => {
      button.removeEventListener("click", onClick);
      group.removeEventListener("pointerenter", onPointerEnter);
      group.removeEventListener("pointerleave", onPointerLeave);
      group.removeEventListener("keydown", onKeyDown);
      group.removeEventListener("focusout", onFocusOut);
    });
  }

  const onDocumentPointerDown = (event: Event) => {
    if (!(event.target instanceof Node)) return;
    for (const entry of entries) {
      if (isOpen(entry) && !entry.group.contains(event.target)) {
        setOpen(entry, false);
      }
    }
  };

  const onViewportChange = () => closeAll();

  document.addEventListener("pointerdown", onDocumentPointerDown);
  if (typeof desktopMQ.addEventListener === "function") {
    desktopMQ.addEventListener("change", onViewportChange);
  }

  return () => {
    for (const cleanup of cleanups) cleanup();
    document.removeEventListener("pointerdown", onDocumentPointerDown);
    if (typeof desktopMQ.removeEventListener === "function") {
      desktopMQ.removeEventListener("change", onViewportChange);
    }
    closeAll();
  };
}
