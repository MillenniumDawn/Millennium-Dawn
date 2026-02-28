import { visit } from "unist-util-visit";

const BASE = "/Millennium-Dawn";
const ABSOLUTE_SCHEME = /^[a-zA-Z][a-zA-Z0-9+.-]*:/;

function withBase(url: string | undefined): string | undefined {
  if (!url || typeof url !== "string") return url;
  if (url.startsWith("#")) return url;
  if (url.startsWith("//")) return url;
  if (ABSOLUTE_SCHEME.test(url)) return url;
  if (!url.startsWith("/")) return url;
  if (url === BASE || url.startsWith(`${BASE}/`)) return url;
  if (url === "/") return `${BASE}/`;
  return `${BASE}${url}`;
}

function rewriteHtmlLiteral(value: string | undefined): string | undefined {
  if (!value || typeof value !== "string") return value;
  return value
    .replace(/\shref="\/(?!Millennium-Dawn)([^"]*)"/g, (_m, tail) => ` href="${withBase(`/${tail}`)}"`)
    .replace(/\ssrc="\/(?!Millennium-Dawn)([^"]*)"/g, (_m, tail) => ` src="${withBase(`/${tail}`)}"`);
}

export function remarkRootRelativeToBase() {
  return (tree: unknown) => {
    visit(tree as any, "link", (node: any) => {
      node.url = withBase(node.url);
    });

    visit(tree as any, "image", (node: any) => {
      node.url = withBase(node.url);
    });

    visit(tree as any, "definition", (node: any) => {
      node.url = withBase(node.url);
    });

    visit(tree as any, "html", (node: any) => {
      node.value = rewriteHtmlLiteral(node.value);
    });
  };
}
