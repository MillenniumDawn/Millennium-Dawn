export { initMobileNavigation } from "./mobile-nav";

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
