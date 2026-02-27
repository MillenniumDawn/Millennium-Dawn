import type { MarkdownHeading } from "astro";

type TocItem = {
  id: string;
  text: string;
  depth: number;
  children: TocItem[];
  sublistId?: number;
};

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function normalizeHeadings(headings: MarkdownHeading[]): MarkdownHeading[] {
  return headings.filter((heading) => {
    const hasText = typeof heading.text === "string" && heading.text.trim().length > 0;
    const hasSlug = typeof heading.slug === "string" && heading.slug.trim().length > 0;
    return hasText && hasSlug && heading.depth >= 2 && heading.depth <= 4;
  });
}

function assignSublistIds(items: TocItem[]): void {
  let currentId = 0;

  const walk = (nodes: TocItem[]) => {
    nodes.forEach((node) => {
      if (!node.children.length) return;
      node.sublistId = currentId;
      currentId += 1;
      walk(node.children);
    });
  };

  walk(items);
}

export function buildTocTree(headings: MarkdownHeading[]): TocItem[] {
  const normalized = normalizeHeadings(headings);
  const tree: TocItem[] = [];
  const stack: TocItem[] = [];

  normalized.forEach((heading) => {
    const item: TocItem = {
      id: heading.slug,
      text: heading.text.trim(),
      depth: heading.depth,
      children: [],
    };

    while (stack.length && stack[stack.length - 1].depth >= item.depth) {
      stack.pop();
    }

    if (!stack.length) {
      tree.push(item);
    } else {
      stack[stack.length - 1].children.push(item);
    }

    stack.push(item);
  });

  assignSublistIds(tree);
  return tree;
}

export function renderTocHtml(headings: MarkdownHeading[]): string {
  const tree = buildTocTree(headings);
  if (!tree.length) return "";

  const renderList = (items: TocItem[], depth: number, sublistId?: number): string => {
    const cls = depth === 0 ? "toc-sidebar__list" : "toc-sidebar__sublist";
    const attrs = depth === 0 ? "" : ` data-toc-sublist="${sublistId}"`;
    let html = `<ul class="${cls}" role="list"${attrs}>`;

    items.forEach((item) => {
      const hasChildren = item.children.length > 0;
      const itemClass = hasChildren ? "toc-sidebar__item toc-sidebar__item--parent" : "toc-sidebar__item";
      const text = escapeHtml(item.text);
      const id = escapeHtml(item.id);

      let linkClass = "toc-sidebar__link";
      if (depth === 1) linkClass += " toc-sidebar__sublink";
      if (depth >= 2) linkClass += " toc-sidebar__sublink toc-sidebar__sublink--deep";

      html += `<li class="${itemClass}" role="listitem">`;

      if (hasChildren && typeof item.sublistId === "number") {
        html += '<div class="toc-sidebar__row">';
        html += `<a href="#${id}" class="${linkClass}" data-toc-id="${id}" title="${text}">${text}</a>`;
        html += '<button class="toc-sidebar__expand" aria-expanded="false"';
        html += ` aria-label="Expand: ${text}" data-toc-expand="${item.sublistId}" type="button">`;
        html += '<svg aria-hidden="true" width="12" height="12" viewBox="0 0 12 12">';
        html += '<path d="M4.5 2l4 4-4 4" stroke="currentColor" stroke-width="1.5"';
        html += ' fill="none" stroke-linecap="round" stroke-linejoin="round"/>';
        html += "</svg></button>";
        html += "</div>";
        html += renderList(item.children, depth + 1, item.sublistId);
      } else {
        html += `<a href="#${id}" class="${linkClass}" data-toc-id="${id}" title="${text}">${text}</a>`;
      }

      html += "</li>";
    });

    html += "</ul>";
    return html;
  };

  return renderList(tree, 0);
}
