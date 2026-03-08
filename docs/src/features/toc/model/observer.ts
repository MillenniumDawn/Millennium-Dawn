import type { TocEntry } from "./types";

type ActiveSetter = (entry: TocEntry | null) => void;

export interface TocObserverHandle {
  cleanup(): void;
}

export function initTocObserver(
  headingEntries: TocEntry[],
  entryById: Record<string, TocEntry>,
  scrollOffset: number,
  setActive: ActiveSetter,
): TocObserverHandle {
  const findActiveFallback = (): TocEntry | null => {
    for (let i = headingEntries.length - 1; i >= 0; i -= 1) {
      if (headingEntries[i].el.getBoundingClientRect().top <= scrollOffset) {
        return headingEntries[i];
      }
    }
    return headingEntries[0] || null;
  };

  const visibleHeadings = new Map<string, number>();
  let observer: IntersectionObserver | null = null;
  let currentActive: TocEntry | null = null;

  const wrappedSetActive = (entry: TocEntry | null) => {
    currentActive = entry;
    setActive(entry);
  };

  const pickVisibleActive = (): TocEntry | null => {
    if (!visibleHeadings.size) {
      if ((window.scrollY ?? 0) < 32) return headingEntries[0] ?? null;
      return currentActive ?? findActiveFallback();
    }

    let bestEntry: TocEntry | null = null;
    let bestDistance = Number.POSITIVE_INFINITY;

    visibleHeadings.forEach((top, id) => {
      const entry = entryById[id];
      if (!entry) return;
      const distance = Math.abs(top - scrollOffset);
      if (distance < bestDistance) {
        bestDistance = distance;
        bestEntry = entry;
      }
    });

    return bestEntry ?? currentActive ?? findActiveFallback();
  };

  if (typeof IntersectionObserver !== "undefined") {
    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!(entry.target instanceof HTMLElement)) return;
          const target = entry.target;
          if (entry.isIntersecting) {
            visibleHeadings.set(target.id, entry.boundingClientRect.top);
          } else {
            visibleHeadings.delete(target.id);
          }
        });
        wrappedSetActive(pickVisibleActive());
      },
      {
        root: null,
        rootMargin: `-${scrollOffset}px 0px -55% 0px`,
        threshold: [0, 1],
      },
    );

    headingEntries.forEach((entry) => observer?.observe(entry.el));
    wrappedSetActive(headingEntries[0]);
  } else {
    wrappedSetActive(findActiveFallback());
  }

  let rafPending = false;
  const onScroll = () => {
    if (rafPending) return;
    rafPending = true;
    requestAnimationFrame(() => {
      rafPending = false;
      if (!observer) wrappedSetActive(findActiveFallback());
    });
  };

  const onResize = () => {
    if (!observer) wrappedSetActive(findActiveFallback());
  };

  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onResize);

  return {
    cleanup() {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onResize);
      observer?.disconnect();
    },
  };
}
