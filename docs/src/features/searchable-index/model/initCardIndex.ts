type Cleanup = () => void;
const NOOP: Cleanup = () => {};

interface CardIndexDomRefs {
  cards: HTMLElement[];
  filterInput: HTMLInputElement | null;
  emptyState: HTMLElement | null;
  prevBtn: HTMLButtonElement | null;
  nextBtn: HTMLButtonElement | null;
  status: HTMLElement | null;
  pageSize: number;
}

interface CardIndexState {
  currentPage: number;
  activeQuery: string;
}

function getFirst<T extends HTMLElement>(root: ParentNode, selector: string): T | null {
  return root.querySelector<T>(selector);
}

function getAll<T extends HTMLElement>(root: ParentNode, selector: string): T[] {
  return Array.from(root.querySelectorAll<T>(selector));
}

function resolvePageSize(root: HTMLElement): number {
  const pageSize = Number.parseInt(root.getAttribute("data-page-size") ?? "8", 10);
  return Number.isFinite(pageSize) && pageSize > 0 ? pageSize : 8;
}

function getMatches(cards: HTMLElement[], query: string): HTMLElement[] {
  if (!query) return cards.slice();

  return cards.filter((card) => {
    const haystack = (card.getAttribute("data-search") ?? "").toLowerCase();
    return haystack.includes(query);
  });
}

function updateCardVisibility(cards: HTMLElement[], matches: HTMLElement[], start: number, end: number): void {
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
}

function renderCardIndex(dom: CardIndexDomRefs, state: CardIndexState): void {
  const matches = getMatches(dom.cards, state.activeQuery);
  const totalPages = Math.max(1, Math.ceil(matches.length / dom.pageSize));
  if (state.currentPage > totalPages) state.currentPage = totalPages;
  if (state.currentPage < 1) state.currentPage = 1;

  const start = (state.currentPage - 1) * dom.pageSize;
  const end = start + dom.pageSize;
  updateCardVisibility(dom.cards, matches, start, end);

  if (dom.emptyState) dom.emptyState.hidden = matches.length > 0;
  if (dom.prevBtn) dom.prevBtn.disabled = state.currentPage <= 1 || matches.length === 0;
  if (dom.nextBtn) dom.nextBtn.disabled = state.currentPage >= totalPages || matches.length === 0;

  if (dom.status) {
    dom.status.textContent = matches.length
      ? `Page ${state.currentPage} of ${totalPages} (${matches.length} matches)`
      : "No matches";
  }
}

function initCardIndexRoot(root: HTMLElement): Cleanup {
  const cards = getAll(root, "[data-card-item]");
  if (!cards.length) return NOOP;

  const dom: CardIndexDomRefs = {
    cards,
    filterInput: getFirst<HTMLInputElement>(root, "[data-card-filter]"),
    emptyState: getFirst(root, "[data-card-empty]"),
    prevBtn: getFirst<HTMLButtonElement>(root, "[data-card-prev]"),
    nextBtn: getFirst<HTMLButtonElement>(root, "[data-card-next]"),
    status: getFirst(root, "[data-card-status]"),
    pageSize: resolvePageSize(root),
  };
  const state: CardIndexState = {
    currentPage: 1,
    activeQuery: "",
  };

  const onFilterInput = () => {
    if (!dom.filterInput) return;
    state.activeQuery = (dom.filterInput.value || "").trim().toLowerCase();
    state.currentPage = 1;
    renderCardIndex(dom, state);
  };

  const onPrevClick = () => {
    state.currentPage -= 1;
    renderCardIndex(dom, state);
  };

  const onNextClick = () => {
    state.currentPage += 1;
    renderCardIndex(dom, state);
  };

  if (dom.filterInput) {
    dom.filterInput.addEventListener("input", onFilterInput);
  }
  if (dom.prevBtn) {
    dom.prevBtn.addEventListener("click", onPrevClick);
  }
  if (dom.nextBtn) {
    dom.nextBtn.addEventListener("click", onNextClick);
  }

  renderCardIndex(dom, state);

  return () => {
    if (dom.filterInput) {
      dom.filterInput.removeEventListener("input", onFilterInput);
    }
    if (dom.prevBtn) {
      dom.prevBtn.removeEventListener("click", onPrevClick);
    }
    if (dom.nextBtn) {
      dom.nextBtn.removeEventListener("click", onNextClick);
    }
  };
}

export function initCardIndex(): Cleanup {
  const cleanups = getAll(document, "[data-card-index]")
    .map((root) => initCardIndexRoot(root))
    .filter((cleanup) => cleanup !== NOOP);

  if (!cleanups.length) return NOOP;

  return () => {
    while (cleanups.length) {
      const cleanup = cleanups.pop();
      if (cleanup) cleanup();
    }
  };
}
