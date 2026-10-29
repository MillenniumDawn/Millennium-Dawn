import { buildTocTree, type TocHeadingLike, type TocTreeItem } from "@/shared/lib/content/toc";
import { TOC_ATTRS, TOC_HEADING_RANGE, TOC_LABELS } from "./config";

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

const EXPAND_ICON =
  '<svg aria-hidden="true" class="toc-expand-icon" viewBox="0 0 12 12"><path d="M4.5 2l4 4-4 4" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>';

function getLinkClass(depth: number): string {
  if (depth === 1) return "toc-link toc-link-1";
  if (depth >= 2) return "toc-link toc-link-2";
  return "toc-link";
}

export function renderTocTreeHtml(tree: TocTreeItem[]): string {
  if (!tree.length) return "";

  let nextSublistId = 0;

  const renderList = (items: TocTreeItem[], depth: number, sublistId?: number): string => {
    const listClass = depth === 0 ? "toc-tree" : "toc-sub";
    const sublistAttr = depth === 0 ? "" : ` ${TOC_ATTRS.sublist}="${sublistId}"`;
    let html = `<ul class="${listClass}"${sublistAttr}>`;

    items.forEach((item) => {
      const hasChildren = item.children.length > 0;
      const text = escapeHtml(item.text);
      const id = escapeHtml(item.id);

      html += `<li class="toc-item">`;

      if (hasChildren) {
        const currentSublistId = nextSublistId;
        nextSublistId += 1;

        html += `<div class="toc-row">`;
        html += `<a href="#${id}" class="${getLinkClass(depth)}" ${TOC_ATTRS.link} ${TOC_ATTRS.tocId}="${id}">${text}</a>`;
        html += `<button class="toc-expand" aria-expanded="false" aria-label="${escapeHtml(TOC_LABELS.expand(item.text))}" ${TOC_ATTRS.expand}="${currentSublistId}" type="button">${EXPAND_ICON}</button>`;
        html += `</div>`;
        html += renderList(item.children, depth + 1, currentSublistId);
      } else {
        html += `<a href="#${id}" class="${getLinkClass(depth)}" ${TOC_ATTRS.link} ${TOC_ATTRS.tocId}="${id}">${text}</a>`;
      }

      html += "</li>";
    });

    html += "</ul>";
    return html;
  };

  return renderList(tree, 0);
}

export function renderTocHtml(headings: TocHeadingLike[]): string {
  return renderTocTreeHtml(buildTocTree(headings, TOC_HEADING_RANGE));
}

export type { TocHeadingLike, TocTreeItem };
