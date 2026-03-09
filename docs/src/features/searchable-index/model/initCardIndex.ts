type Cleanup = () => void;

function getFirst<T extends HTMLElement>(root: ParentNode, selector: string): T | null {
  return root.querySelector<T>(selector);
}

function getAll<T extends HTMLElement>(root: ParentNode, selector: string): T[] {
  return Array.from(root.querySelectorAll<T>(selector));
}

export function initCardIndex(): Cleanup {
  const roots = getAll(document, "[data-card-index]");
  if (!roots.length) return () => {};

  const cleanups: Cleanup[] = [];

  roots.forEach((root) => {
    const cards = getAll(root, "[data-card-item]");
    if (!cards.length) return;

    const filterInput = getFirst<HTMLInputElement>(root, "[data-card-filter]");
    const emptyState = getFirst(root, "[data-card-empty]");
    const prevBtn = getFirst<HTMLButtonElement>(root, "[data-card-prev]");
    const nextBtn = getFirst<HTMLButtonElement>(root, "[data-card-next]");
    const status = getFirst(root, "[data-card-status]");

    let pageSize = Number.parseInt(root.getAttribute("data-page-size") ?? "8", 10);
    if (!Number.isFinite(pageSize) || pageSize < 1) pageSize = 8;

    let currentPage = 1;
    let activeQuery = "";

    const getMatches = (): HTMLElement[] => {
      if (!activeQuery) return cards.slice();

      return cards.filter((card) => {
        const haystack = (card.getAttribute("data-search") ?? "").toLowerCase();
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

    const onFilterInput = () => {
      if (!filterInput) return;
      activeQuery = (filterInput.value || "").trim().toLowerCase();
      currentPage = 1;
      render();
    };

    const onPrevClick = () => {
      currentPage -= 1;
      render();
    };

    const onNextClick = () => {
      currentPage += 1;
      render();
    };

    if (filterInput) {
      filterInput.addEventListener("input", onFilterInput);
    }

    if (prevBtn) {
      prevBtn.addEventListener("click", onPrevClick);
    }

    if (nextBtn) {
      nextBtn.addEventListener("click", onNextClick);
    }

    cleanups.push(() => {
      if (filterInput) {
        filterInput.removeEventListener("input", onFilterInput);
      }
      if (prevBtn) {
        prevBtn.removeEventListener("click", onPrevClick);
      }
      if (nextBtn) {
        nextBtn.removeEventListener("click", onNextClick);
      }
    });

    render();
  });

  return () => {
    while (cleanups.length) {
      const cleanup = cleanups.pop();
      if (cleanup) cleanup();
    }
  };
}
