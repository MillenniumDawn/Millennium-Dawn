import { buildTocTree, type TocHeadingLike, type TocTreeItem } from "@/shared/lib/toc";
import { TOC_ATTRS, TOC_HEADING_RANGE, TOC_SELECTORS, TOC_STATES } from "../lib/config";
import { renderTocTreeHtml } from "../lib/render";

type Cleanup = () => void;

function toTocHeading(heading: HTMLHeadingElement): TocHeadingLike | null {
  const depth = Number.parseInt(heading.tagName.charAt(1), 10);
  const text = (heading.textContent || "").trim();
  const slug = heading.id;

  if (!text || !slug || depth < TOC_HEADING_RANGE.minDepth || depth > TOC_HEADING_RANGE.maxDepth) {
    return null;
  }

  return {
    depth,
    slug,
    text,
  };
}

export type { TocTreeItem };

export function buildTree(headings: HTMLHeadingElement[]): TocTreeItem[] {
  const tocHeadings = headings
    .map(toTocHeading)
    .filter((heading): heading is TocHeadingLike => heading !== null);

  return buildTocTree(tocHeadings, TOC_HEADING_RANGE);
}

export function renderNav(nav: HTMLElement, tree: TocTreeItem[]): void {
  nav.innerHTML = renderTocTreeHtml(tree);
}

export function toggleSublist(button: HTMLElement, sublist: HTMLElement | null, open: boolean): void {
  if (!sublist) return;
  button.setAttribute("aria-expanded", open ? "true" : "false");

  if (open) {
    sublist.classList.add(TOC_STATES.expanded);
    sublist.style.maxHeight = `${sublist.scrollHeight}px`;
    sublist.style.opacity = "1";

    const onEnd = () => {
      sublist.style.maxHeight = "none";
      sublist.removeEventListener("transitionend", onEnd);
    };

    sublist.addEventListener("transitionend", onEnd);
  } else {
    sublist.style.maxHeight = `${sublist.scrollHeight}px`;
    void sublist.offsetHeight;
    sublist.style.maxHeight = "0";
    sublist.style.opacity = "0";

    const onEnd = () => {
      sublist.classList.remove(TOC_STATES.expanded);
      sublist.removeEventListener("transitionend", onEnd);
    };

    sublist.addEventListener("transitionend", onEnd);
  }
}

export function bindExpandButtons(nav: HTMLElement): Cleanup {
  const cleanups: Cleanup[] = [];

  nav.querySelectorAll<HTMLButtonElement>(TOC_SELECTORS.expandButton).forEach((button) => {
    const onClick = (event: MouseEvent) => {
      event.preventDefault();
      event.stopPropagation();

      const idx = button.getAttribute(TOC_ATTRS.expand);
      if (!idx) return;

      const sublist = nav.querySelector<HTMLElement>(`[${TOC_ATTRS.sublist}="${idx}"]`);
      const isOpen = button.getAttribute("aria-expanded") === "true";
      toggleSublist(button, sublist, !isOpen);
    };

    button.addEventListener("click", onClick);
    cleanups.push(() => {
      button.removeEventListener("click", onClick);
    });
  });

  return () => {
    while (cleanups.length) {
      const cleanup = cleanups.pop();
      if (cleanup) cleanup();
    }
  };
}
