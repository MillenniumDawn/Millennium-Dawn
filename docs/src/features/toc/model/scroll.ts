import { TOC_ATTRS, TOC_SELECTORS } from "../lib/config";

export interface TocScrollHandle {
  cleanup(): void;
}

export function initTocScroll(
  nav: HTMLElement,
  progress: HTMLElement | null,
  scrollOffset: number,
): TocScrollHandle {
  const updateProgress = () => {
    if (!progress) return;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const pct = docHeight > 0 ? Math.min(100, ((window.scrollY || 0) / docHeight) * 100) : 0;
    progress.style.width = `${pct}%`;
  };

  const onNavLinkClick = (event: MouseEvent) => {
    if (!(event.target instanceof Element)) return;
    const link = event.target.closest<HTMLAnchorElement>(TOC_SELECTORS.link);
    if (!link) return;

    event.preventDefault();

    const targetId = link.getAttribute(TOC_ATTRS.tocId);
    if (!targetId) return;

    const target = document.getElementById(targetId);
    if (!(target instanceof HTMLElement)) return;

    const header = document.querySelector<HTMLElement>(TOC_SELECTORS.header);
    const offset = header ? header.offsetHeight + 16 : scrollOffset;
    const targetTop = target.getBoundingClientRect().top + window.pageYOffset - offset;
    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: targetTop, behavior: prefersReduced ? "auto" : "smooth" });

    if (history.replaceState) history.replaceState(null, "", `#${targetId}`);

    target.setAttribute("tabindex", "-1");
    target.focus({ preventScroll: true });
  };

  nav.addEventListener("click", onNavLinkClick);

  let rafPending = false;
  const onScroll = () => {
    if (rafPending) return;
    rafPending = true;
    requestAnimationFrame(() => {
      rafPending = false;
      updateProgress();
    });
  };

  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", updateProgress);
  updateProgress();

  return {
    cleanup() {
      nav.removeEventListener("click", onNavLinkClick);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", updateProgress);
    },
  };
}
