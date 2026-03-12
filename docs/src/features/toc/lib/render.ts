import { buildTocTree, type TocHeadingLike, type TocTreeItem } from "../../../shared/lib/toc";
import { TOC_ATTRS, TOC_CLASSES, TOC_HEADING_RANGE, TOC_LABELS } from "./config";

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function getLinkClass(depth: number): string {
  let linkClass = TOC_CLASSES.link;

  if (depth === 1) {
    linkClass += ` ${TOC_CLASSES.sublink}`;
  } else if (depth >= 2) {
    linkClass += ` ${TOC_CLASSES.sublink} ${TOC_CLASSES.deepSublink}`;
  }

  return linkClass;
}

export function renderTocTreeHtml(tree: TocTreeItem[]): string {
  if (!tree.length) return "";

  let nextSublistId = 0;

  const renderList = (items: TocTreeItem[], depth: number, sublistId?: number): string => {
    const listClass = depth === 0 ? TOC_CLASSES.list : TOC_CLASSES.sublist;
    const sublistAttr = depth === 0 ? "" : ` ${TOC_ATTRS.sublist}="${sublistId}"`;
    let html = `<ul class="${listClass}" role="list"${sublistAttr}>`;

    items.forEach((item) => {
      const hasChildren = item.children.length > 0;
      const itemClass = hasChildren ? `${TOC_CLASSES.item} ${TOC_CLASSES.parentItem}` : TOC_CLASSES.item;
      const text = escapeHtml(item.text);
      const id = escapeHtml(item.id);

      html += `<li class="${itemClass}" role="listitem">`;

      if (hasChildren) {
        const currentSublistId = nextSublistId;
        nextSublistId += 1;

        html += `<div class="${TOC_CLASSES.row}">`;
        html += `<a href="#${id}" class="${getLinkClass(depth)}" ${TOC_ATTRS.tocId}="${id}" title="${text}">${text}</a>`;
        html += `<button class="${TOC_CLASSES.expandButton}" aria-expanded="false" aria-label="${escapeHtml(TOC_LABELS.expand(item.text))}" ${TOC_ATTRS.expand}="${currentSublistId}" type="button">`;
        html += '<svg aria-hidden="true" width="12" height="12" viewBox="0 0 12 12">';
        html += '<path d="M4.5 2l4 4-4 4" stroke="currentColor" stroke-width="1.5"';
        html += ' fill="none" stroke-linecap="round" stroke-linejoin="round"/>';
        html += "</svg></button>";
        html += "</div>";
        html += renderList(item.children, depth + 1, currentSublistId);
      } else {
        html += `<a href="#${id}" class="${getLinkClass(depth)}" ${TOC_ATTRS.tocId}="${id}" title="${text}">${text}</a>`;
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
