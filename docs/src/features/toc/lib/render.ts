import { buildTocTree, type TocHeadingLike, type TocTreeItem } from "@/shared/lib/toc";
import { FOCUS_RING_CLASS } from "@/shared/ui/tailwind";
import { TOC_ATTRS, TOC_HEADING_RANGE, TOC_LABELS } from "./config";

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

const TOC_LIST_CLASS = "m-0 list-none p-0";

const TOC_SUBLIST_CLASS = [
  TOC_LIST_CLASS,
  "max-h-0",
  "overflow-hidden",
  "opacity-0",
  "transition-[max-height,opacity]",
  "duration-toc",
  "ease-[cubic-bezier(0.4,0,0.2,1)]",
  "[&.is-expanded]:opacity-100",
].join(" ");

const TOC_ITEM_CLASS = "m-0 p-0";

const TOC_ROW_CLASS = "flex min-w-0 items-start";

const TOC_LINK_BASE_CLASS = [
  "block",
  "min-h-9",
  "border-l-[3px]",
  "border-transparent",
  "px-[0.85rem]",
  "py-[0.4rem]",
  "text-[0.84rem]",
  "leading-[1.5]",
  "text-text-secondary",
  "no-underline",
  "transition-[color,background-color,border-color]",
  "duration-200",
  "ease-[cubic-bezier(0.4,0,0.2,1)]",
  "hover:bg-primary-light",
  "hover:text-primary",
  "hover:no-underline",
  "overflow-hidden",
  "[display:-webkit-box]",
  "[overflow-wrap:anywhere]",
  "[word-break:break-word]",
  "[-webkit-box-orient:vertical]",
  "[-webkit-line-clamp:var(--toc-line-clamp,3)]",
  "[&.is-active]:border-primary",
  "[&.is-active]:bg-primary-light",
  "[&.is-active]:font-semibold",
  "[&.is-active]:text-primary",
  FOCUS_RING_CLASS,
].join(" ");

const TOC_EXPAND_BUTTON_CLASS = [
  "flex",
  "min-h-9",
  "min-w-9",
  "shrink-0",
  "items-center",
  "justify-center",
  "px-md",
  "text-text-muted",
  "transition-[color,background-color]",
  "duration-200",
  "ease-[cubic-bezier(0.4,0,0.2,1)]",
  "hover:bg-primary-light",
  "hover:text-primary",
  "[&[aria-expanded=true]>svg]:rotate-90",
  FOCUS_RING_CLASS,
].join(" ");

function getLinkClass(depth: number): string {
  if (depth === 1) {
    return [
      TOC_LINK_BASE_CLASS,
      "pl-[calc(0.85rem+0.85rem)]",
      "text-[0.81rem]",
      "[-webkit-line-clamp:2]",
    ].join(" ");
  }

  if (depth >= 2) {
    return [
      TOC_LINK_BASE_CLASS,
      "pl-[calc(0.85rem+1.7rem)]",
      "text-[0.78rem]",
      "text-text-muted",
      "[-webkit-line-clamp:2]",
      "[&.is-active]:text-primary",
    ].join(" ");
  }

  return TOC_LINK_BASE_CLASS;
}

export function renderTocTreeHtml(tree: TocTreeItem[]): string {
  if (!tree.length) return "";

  let nextSublistId = 0;

  const renderList = (items: TocTreeItem[], depth: number, sublistId?: number): string => {
    const listClass = depth === 0 ? TOC_LIST_CLASS : TOC_SUBLIST_CLASS;
    const sublistAttr = depth === 0 ? "" : ` ${TOC_ATTRS.sublist}="${sublistId}"`;
    let html = `<ul class="${listClass}" role="list"${sublistAttr}>`;

    items.forEach((item) => {
      const hasChildren = item.children.length > 0;
      const text = escapeHtml(item.text);
      const id = escapeHtml(item.id);

      html += `<li class="${TOC_ITEM_CLASS}" role="listitem">`;

      if (hasChildren) {
        const currentSublistId = nextSublistId;
        nextSublistId += 1;

        html += `<div class="${TOC_ROW_CLASS}">`;
        html += `<a href="#${id}" class="${getLinkClass(depth)}" ${TOC_ATTRS.link} ${TOC_ATTRS.tocId}="${id}" title="${text}">${text}</a>`;
        html += `<button class="${TOC_EXPAND_BUTTON_CLASS}" aria-expanded="false" aria-label="${escapeHtml(TOC_LABELS.expand(item.text))}" ${TOC_ATTRS.expand}="${currentSublistId}" type="button">`;
        html += '<svg aria-hidden="true" class="size-3 shrink-0 transition-transform duration-250 ease-in-out" viewBox="0 0 12 12">';
        html += '<path d="M4.5 2l4 4-4 4" stroke="currentColor" stroke-width="1.5"';
        html += ' fill="none" stroke-linecap="round" stroke-linejoin="round"/>';
        html += "</svg></button>";
        html += "</div>";
        html += renderList(item.children, depth + 1, currentSublistId);
      } else {
        html += `<a href="#${id}" class="${getLinkClass(depth)}" ${TOC_ATTRS.link} ${TOC_ATTRS.tocId}="${id}" title="${text}">${text}</a>`;
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
