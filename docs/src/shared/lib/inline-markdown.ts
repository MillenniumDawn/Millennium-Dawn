import { withBase } from "./urls";

export type InlinePart = { type: "text"; value: string } | { type: "link"; value: string; href: string };

const INLINE_LINK_RE = /\[([^\]]+)\]\(([^)]+)\)/g;

function isSafeHref(href: string): boolean {
  return /^(https?:\/\/|mailto:|\/|#)/i.test(href.trim());
}

function resolveInlineHref(href: string): string {
  return href.startsWith("/") ? withBase(href) : href;
}

export function parseInlineMarkdown(text: string): InlinePart[] {
  const source = text || "";
  const parts: InlinePart[] = [];
  let lastIndex = 0;

  INLINE_LINK_RE.lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = INLINE_LINK_RE.exec(source)) !== null) {
    if (match.index > lastIndex) {
      parts.push({ type: "text", value: source.slice(lastIndex, match.index) });
    }

    const label = match[1] || "";
    const href = (match[2] || "").trim();

    if (isSafeHref(href)) {
      parts.push({ type: "link", value: label, href: resolveInlineHref(href) });
    } else {
      parts.push({ type: "text", value: `[${label}](${href})` });
    }

    lastIndex = INLINE_LINK_RE.lastIndex;
  }

  if (lastIndex < source.length) {
    parts.push({ type: "text", value: source.slice(lastIndex) });
  }

  return parts;
}
