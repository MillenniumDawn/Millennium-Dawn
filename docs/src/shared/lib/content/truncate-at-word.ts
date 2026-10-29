const ELLIPSIS = "…";

export function truncateAtWord(text: string, maxLength: number): string {
  const trimmed = text.trim();
  if (trimmed.length <= maxLength) {
    return trimmed;
  }

  const slice = trimmed.slice(0, maxLength);
  const lastSpace = slice.lastIndexOf(" ");
  const cutIndex = lastSpace > Math.floor(maxLength * 0.6) ? lastSpace : maxLength;
  return trimmed.slice(0, cutIndex).trimEnd() + ELLIPSIS;
}
