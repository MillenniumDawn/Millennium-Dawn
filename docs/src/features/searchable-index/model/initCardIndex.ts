import {
  SEARCH_INDEX_PAGINATION_ELLIPSIS_CLASS,
  SEARCH_INDEX_PAGINATION_PAGE_BUTTON_CLASS,
} from "@/shared/ui/tailwind";

type Cleanup = () => void;
const NOOP: Cleanup = () => {};

interface CardIndexDomRefs {
  list: HTMLElement | null;
  cards: HTMLElement[];
  filterInput: HTMLInputElement | null;
  emptyState: HTMLElement | null;
  pagination: HTMLElement | null;
  prevBtn: HTMLButtonElement | null;
  nextBtn: HTMLButtonElement | null;
  status: HTMLElement | null;
  results: HTMLElement | null;
  pages: HTMLElement | null;
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

type PageToken = number | "ellipsis";

function buildPageTokens(pageCount: number, currentPage: number): PageToken[] {
  if (pageCount <= 5) return Array.from({ length: pageCount }, (_, index) => index + 1);

  const pages = new Set<number>([1, pageCount, currentPage - 1, currentPage, currentPage + 1]);
  const sorted = Array.from(pages)
    .filter((page) => page >= 1 && page <= pageCount)
    .sort((left, right) => left - right);

  const tokens: PageToken[] = [];

  sorted.forEach((page, index) => {
    const previous = sorted[index - 1];
    if (previous && page - previous > 1) tokens.push("ellipsis");
    tokens.push(page);
  });

  return tokens;
}

function renderPageButtons(container: HTMLElement, pageCount: number, currentPage: number): void {
  const fragment = document.createDocumentFragment();

  buildPageTokens(pageCount, currentPage).forEach((token) => {
    if (token === "ellipsis") {
      const ellipsis = document.createElement("span");
      ellipsis.className = SEARCH_INDEX_PAGINATION_ELLIPSIS_CLASS;
      ellipsis.setAttribute("aria-hidden", "true");
      ellipsis.textContent = "…";
      fragment.append(ellipsis);
      return;
    }

    const button = document.createElement("button");
    button.type = "button";
    button.className = SEARCH_INDEX_PAGINATION_PAGE_BUTTON_CLASS;
    button.dataset.cardPage = String(token);
    button.setAttribute("aria-label", `Go to page ${token}`);
    button.textContent = String(token);

    if (token === currentPage) {
      button.setAttribute("aria-current", "page");
    }

    fragment.append(button);
  });

  container.replaceChildren(fragment);
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

function lockListHeight(list: HTMLElement | null, cards: HTMLElement[], matches: HTMLElement[], pageSize: number, currentStart: number, currentEnd: number): void {
  if (!list) return;

  if (!matches.length) {
    list.style.minHeight = "0px";
    return;
  }

  let tallestPageHeight = 0;

  for (let start = 0; start < matches.length; start += pageSize) {
    const end = start + pageSize;
    updateCardVisibility(cards, matches, start, end);
    tallestPageHeight = Math.max(tallestPageHeight, Math.ceil(list.getBoundingClientRect().height));
  }

  updateCardVisibility(cards, matches, currentStart, currentEnd);
  list.style.minHeight = tallestPageHeight > 0 ? `${tallestPageHeight}px` : "0px";
}

function renderCardIndex(dom: CardIndexDomRefs, state: CardIndexState): void {
  const matches = getMatches(dom.cards, state.activeQuery);
  const totalPages = Math.max(1, Math.ceil(matches.length / dom.pageSize));
  if (state.currentPage > totalPages) state.currentPage = totalPages;
  if (state.currentPage < 1) state.currentPage = 1;

  const start = (state.currentPage - 1) * dom.pageSize;
  const end = start + dom.pageSize;
  updateCardVisibility(dom.cards, matches, start, end);
  lockListHeight(dom.list, dom.cards, matches, dom.pageSize, start, end);

  if (dom.emptyState) dom.emptyState.hidden = matches.length > 0;
  if (dom.pagination) dom.pagination.hidden = matches.length <= dom.pageSize;
  if (dom.prevBtn) dom.prevBtn.disabled = state.currentPage <= 1 || matches.length === 0;
  if (dom.nextBtn) dom.nextBtn.disabled = state.currentPage >= totalPages || matches.length === 0;

  if (dom.status) {
    dom.status.textContent = matches.length
      ? `Page ${state.currentPage} of ${totalPages}`
      : "No matches";
  }

  if (dom.results) {
    dom.results.textContent = matches.length
      ? `Showing ${start + 1}-${Math.min(end, matches.length)} of ${matches.length}`
      : "Showing 0 of 0";
  }

  if (dom.pages) {
    renderPageButtons(dom.pages, totalPages, state.currentPage);
  }
}

function initCardIndexRoot(root: HTMLElement): Cleanup {
  const cards = getAll(root, "[data-card-item]");
  if (!cards.length) return NOOP;

  const dom: CardIndexDomRefs = {
    list: getFirst(root, "[data-card-list]"),
    cards,
    filterInput: getFirst<HTMLInputElement>(root, "[data-card-filter]"),
    emptyState: getFirst(root, "[data-card-empty]"),
    pagination: getFirst(root, "[data-card-pagination]"),
    prevBtn: getFirst<HTMLButtonElement>(root, "[data-card-prev]"),
    nextBtn: getFirst<HTMLButtonElement>(root, "[data-card-next]"),
    status: getFirst(root, "[data-card-status]"),
    results: getFirst(root, "[data-card-results]"),
    pages: getFirst(root, "[data-card-pages]"),
    pageSize: resolvePageSize(root),
  };
  const state: CardIndexState = {
    currentPage: 1,
    activeQuery: "",
  };
  let resizeFrame = 0;

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

  const onPagesClick = (event: Event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;

    const pageButton = target.closest<HTMLElement>("[data-card-page]");
    if (!pageButton) return;

    const nextPage = Number.parseInt(pageButton.dataset.cardPage ?? "", 10);
    if (!Number.isFinite(nextPage)) return;

    state.currentPage = nextPage;
    renderCardIndex(dom, state);
  };

  const onWindowResize = () => {
    if (resizeFrame) cancelAnimationFrame(resizeFrame);

    resizeFrame = requestAnimationFrame(() => {
      resizeFrame = 0;
      renderCardIndex(dom, state);
    });
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
  if (dom.pages) {
    dom.pages.addEventListener("click", onPagesClick);
  }
  window.addEventListener("resize", onWindowResize);

  renderCardIndex(dom, state);
  root.dataset.cardIndexReady = "true";

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
    if (dom.pages) {
      dom.pages.removeEventListener("click", onPagesClick);
    }
    window.removeEventListener("resize", onWindowResize);
    if (resizeFrame) cancelAnimationFrame(resizeFrame);
    delete root.dataset.cardIndexReady;
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
