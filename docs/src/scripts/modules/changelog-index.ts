function getFirst(root: ParentNode, selectors: string[]): HTMLElement | null {
  for (const selector of selectors) {
    const element = root.querySelector<HTMLElement>(selector);
    if (element) return element;
  }
  return null;
}

function getAll(root: ParentNode, selectors: string[]): HTMLElement[] {
  for (const selector of selectors) {
    const nodes = root.querySelectorAll<HTMLElement>(selector);
    if (nodes.length) return Array.from(nodes);
  }
  return [];
}

export function initCardIndex(): void {
  const roots = getAll(document, ["[data-card-index]", "[data-changelog-index]"]);
  if (!roots.length) return;

  roots.forEach((root) => {
    const cards = getAll(root, ["[data-card-item]", "[data-changelog-card]"]);
    if (!cards.length) return;

    const filterInput = getFirst(root, ["[data-card-filter]", "[data-changelog-filter]"]) as HTMLInputElement | null;
    const emptyState = getFirst(root, ["[data-card-empty]", "[data-changelog-empty]"]);
    const prevBtn = getFirst(root, ["[data-card-prev]", "[data-changelog-prev]"]) as HTMLButtonElement | null;
    const nextBtn = getFirst(root, ["[data-card-next]", "[data-changelog-next]"]) as HTMLButtonElement | null;
    const status = getFirst(root, ["[data-card-status]", "[data-changelog-status]"]);

    let pageSize = Number.parseInt(root.getAttribute("data-page-size") || "8", 10);
    if (!Number.isFinite(pageSize) || pageSize < 1) pageSize = 8;

    let currentPage = 1;
    let activeQuery = "";

    const getMatches = (): HTMLElement[] => {
      if (!activeQuery) return cards.slice();

      return cards.filter((card) => {
        const haystack = (card.getAttribute("data-search") || "").toLowerCase();
        return haystack.includes(activeQuery);
      });
    };

    const render = () => {
      const matches = getMatches();
      const totalPages = Math.max(1, Math.ceil(matches.length / pageSize));
      if (currentPage > totalPages) currentPage = totalPages;
      if (currentPage < 1) currentPage = 1;

      const start = (currentPage - 1) * pageSize;
      const end = start + pageSize;

      cards.forEach((card) => {
        card.hidden = true;
        card.style.display = "none";
        card.setAttribute("aria-hidden", "true");
      });

      matches.slice(start, end).forEach((card) => {
        card.hidden = false;
        card.style.display = "";
        card.removeAttribute("aria-hidden");
      });

      if (emptyState) emptyState.hidden = matches.length > 0;
      if (prevBtn) prevBtn.disabled = currentPage <= 1 || matches.length === 0;
      if (nextBtn) nextBtn.disabled = currentPage >= totalPages || matches.length === 0;

      if (status) {
        status.textContent = matches.length
          ? `Page ${currentPage} of ${totalPages} (${matches.length} matches)`
          : "No matches";
      }
    };

    if (filterInput) {
      filterInput.addEventListener("input", () => {
        activeQuery = (filterInput.value || "").trim().toLowerCase();
        currentPage = 1;
        render();
      });
    }

    if (prevBtn) {
      prevBtn.addEventListener("click", () => {
        currentPage -= 1;
        render();
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener("click", () => {
        currentPage += 1;
        render();
      });
    }

    render();
  });
}

export { initCardIndex as initChangelogIndex };
