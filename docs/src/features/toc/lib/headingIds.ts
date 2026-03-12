import { createUniqueSlugger } from "../../../shared/lib/slugs";
import { TOC_DEFAULTS, TOC_SELECTORS } from "./config";

export function queryTocHeadings(root: ParentNode): HTMLHeadingElement[] {
  return Array.from(root.querySelectorAll<HTMLHeadingElement>(TOC_SELECTORS.headings));
}

export function ensureHeadingIds(headings: HTMLHeadingElement[]): void {
  const existingIds = Array.from(document.querySelectorAll<HTMLElement>("[id]"), (element) => element.id);
  const createId = createUniqueSlugger(existingIds);

  headings.forEach((heading) => {
    if (heading.id) return;
    heading.id = createId(heading.textContent ?? "", TOC_DEFAULTS.fallbackIdBase);
  });
}
