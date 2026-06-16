export type PageToken = number | "ellipsis";

export function buildPageTokens(pageCount: number, currentPage: number): PageToken[] {
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
