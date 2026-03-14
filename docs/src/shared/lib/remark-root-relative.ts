import type { Root } from "mdast";
import { visit } from "unist-util-visit";
import { SITE_BASE_PATH } from "../config/site";

const ABSOLUTE_SCHEME = /^[a-zA-Z][a-zA-Z0-9+.-]*:/;

function createWithBase(base: string): (url: string | undefined) => string | undefined {
  return (url) => {
    if (!url || typeof url !== "string") return url;
    if (url.startsWith("#")) return url;
    if (url.startsWith("//")) return url;
    if (ABSOLUTE_SCHEME.test(url)) return url;
    if (!url.startsWith("/")) return url;
    if (url === base || url.startsWith(`${base}/`)) return url;
    if (url === "/") return `${base}/`;
    return `${base}${url}`;
  };
}

function createRewriteHtml(
  base: string,
  applyBase: (url: string | undefined) => string | undefined,
): (value: string | undefined) => string | undefined {
  const escaped = base.slice(1).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const hrefRe = new RegExp(`\\shref="\\/(?!${escaped})([^"]*)"`, "g");
  const srcRe = new RegExp(`\\ssrc="\\/(?!${escaped})([^"]*)"`, "g");

  return (value) => {
    if (!value || typeof value !== "string") return value;
    return value
      .replace(hrefRe, (_m, tail) => ` href="${applyBase(`/${tail}`)}"`)
      .replace(srcRe, (_m, tail) => ` src="${applyBase(`/${tail}`)}"`);
  };
}

export function remarkRootRelativeToBase(base = SITE_BASE_PATH): (tree: Root) => void {
  const normalized = base.endsWith("/") ? base.slice(0, -1) : base;
  const applyBase = createWithBase(normalized);
  const rewriteHtml = createRewriteHtml(normalized, applyBase);

  return (tree: Root): void => {
    visit(tree, (node) => {
      if (node.type === "link" || node.type === "image" || node.type === "definition") {
        const nextUrl = applyBase(node.url);
        if (nextUrl) {
          node.url = nextUrl;
        }
        return;
      }

      if (node.type === "html") {
        const nextValue = rewriteHtml(node.value);
        if (nextValue) {
          node.value = nextValue;
        }
      }
    });
  };
}
