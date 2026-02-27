export type TocTreeItem = {
  id: string;
  text: string;
  level: number;
  children: TocTreeItem[];
};

function escapeHtml(value: string): string {
  const node = document.createElement("div");
  node.appendChild(document.createTextNode(value));
  return node.innerHTML;
}

export function ensureHeadingIds(headings: HTMLHeadingElement[]): void {
  headings.forEach((heading, index) => {
    if (!heading.id) heading.id = `heading-${index}`;
  });
}

export function buildTree(headings: HTMLHeadingElement[]): TocTreeItem[] {
  const tree: TocTreeItem[] = [];
  let currentH2: TocTreeItem | null = null;
  let currentH3: TocTreeItem | null = null;

  headings.forEach((heading) => {
    const level = Number.parseInt(heading.tagName.charAt(1), 10);
    const item: TocTreeItem = {
      id: heading.id,
      text: (heading.textContent || "").trim(),
      level,
      children: [],
    };

    if (level === 2) {
      currentH2 = item;
      currentH3 = null;
      tree.push(item);
    } else if (level === 3) {
      currentH3 = item;
      (currentH2 ? currentH2.children : tree).push(item);
    } else if (level === 4) {
      const parent = currentH3 || currentH2;
      (parent ? parent.children : tree).push(item);
    }
  });

  return tree;
}

export function renderNav(nav: HTMLElement, tree: TocTreeItem[]): void {
  let sectionIdx = 0;

  const renderList = (items: TocTreeItem[], depth: number): string => {
    const cls = depth === 0 ? "toc-sidebar__list" : "toc-sidebar__sublist";
    let attrs = "";

    if (depth > 0) {
      attrs = ` data-toc-sublist="${sectionIdx}"`;
      sectionIdx++;
    }

    let html = `<ul class="${cls}" role="list"${attrs}>`;

    items.forEach((item) => {
      const hasKids = item.children.length > 0;
      let itemCls = "toc-sidebar__item";
      if (hasKids) itemCls += " toc-sidebar__item--parent";

      let linkCls = "toc-sidebar__link";
      if (depth === 1) linkCls += " toc-sidebar__sublink";
      if (depth >= 2) linkCls += " toc-sidebar__sublink toc-sidebar__sublink--deep";

      html += `<li class="${itemCls}" role="listitem">`;

      if (hasKids) {
        const idx = sectionIdx;
        html += '<div class="toc-sidebar__row">';
        html += `<a href="#${item.id}" class="${linkCls}" data-toc-id="${item.id}" title="${escapeHtml(item.text)}">`;
        html += `${escapeHtml(item.text)}</a>`;
        html += `<button class="toc-sidebar__expand" aria-expanded="false" aria-label="Expand: ${escapeHtml(item.text)}"`;
        html += ` data-toc-expand="${idx}" type="button">`;
        html += '<svg aria-hidden="true" width="12" height="12" viewBox="0 0 12 12">';
        html += '<path d="M4.5 2l4 4-4 4" stroke="currentColor" stroke-width="1.5"';
        html += ' fill="none" stroke-linecap="round" stroke-linejoin="round"/>';
        html += "</svg></button>";
        html += "</div>";
        html += renderList(item.children, depth + 1);
      } else {
        html += `<a href="#${item.id}" class="${linkCls}" data-toc-id="${item.id}" title="${escapeHtml(item.text)}">`;
        html += `${escapeHtml(item.text)}</a>`;
      }

      html += "</li>";
    });

    html += "</ul>";
    return html;
  };

  nav.innerHTML = renderList(tree, 0);
}

export function toggleSublist(button: HTMLElement, sublist: HTMLElement | null, open: boolean): void {
  if (!sublist) return;
  button.setAttribute("aria-expanded", open ? "true" : "false");

  if (open) {
    sublist.classList.add("is-expanded");
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
      sublist.classList.remove("is-expanded");
      sublist.removeEventListener("transitionend", onEnd);
    };

    sublist.addEventListener("transitionend", onEnd);
  }
}

export function bindExpandButtons(nav: HTMLElement): void {
  nav.querySelectorAll<HTMLButtonElement>(".toc-sidebar__expand").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();

      const idx = button.getAttribute("data-toc-expand");
      if (!idx) return;

      const sublist = nav.querySelector<HTMLElement>(`[data-toc-sublist="${idx}"]`);
      const isOpen = button.getAttribute("aria-expanded") === "true";
      toggleSublist(button, sublist, !isOpen);
    });
  });
}
