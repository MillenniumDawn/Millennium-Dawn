function readCssVar(name: string, fallback: string): string {
  const root = document.documentElement;
  if (!root) return fallback;

  const value = getComputedStyle(root).getPropertyValue(name).trim();
  return value || fallback;
}

function parseMs(value: string, fallback: number): number {
  if (!value) return fallback;

  const normalized = value.trim().toLowerCase();
  if (normalized.endsWith("ms")) {
    const milliseconds = parseFloat(normalized.slice(0, -2));
    return Number.isFinite(milliseconds) ? milliseconds : fallback;
  }

  if (normalized.endsWith("s")) {
    const seconds = parseFloat(normalized.slice(0, -1));
    return Number.isFinite(seconds) ? seconds * 1000 : fallback;
  }

  const raw = parseFloat(normalized);
  return Number.isFinite(raw) ? raw : fallback;
}

function parsePx(value: string, fallback: number): number {
  if (!value) return fallback;
  const pixels = parseFloat(value);
  return Number.isFinite(pixels) ? pixels : fallback;
}

export function readCssMsVar(name: string, fallback: number): number {
  return parseMs(readCssVar(name, ""), fallback);
}

export function readCssPxVar(name: string, fallback: number): number {
  return parsePx(readCssVar(name, ""), fallback);
}

export function readCssStringVar(name: string, fallback: string): string {
  return readCssVar(name, fallback);
}
