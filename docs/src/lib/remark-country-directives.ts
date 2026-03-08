import type { Html, Root } from "mdast";
import { load } from "js-yaml";
import { toString } from "mdast-util-to-string";
import { visit } from "unist-util-visit";
import type { Parent } from "unist";

interface SpiritItem {
  name?: string;
  type?: string;
  desc?: string;
}

type DirectiveNode = Parent & {
  type: "containerDirective";
  name?: string;
};

function escapeHtml(value: unknown): string {
  const str = typeof value === "string" ? value : value == null ? "" : `${value as string | number | boolean}`;
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function remarkCountryDirectives(): (tree: Root) => void {
  return (tree: Root): void => {
    visit(tree, (node, index, parent) => {
      if (!parent || typeof index !== "number") return;
      if (node.type !== "containerDirective") return;

      const directiveNode = node as DirectiveNode;
      const directiveParent = parent as Parent;
      if (directiveNode.name !== "spirits") return;

      const raw = toString(directiveNode).trim();
      if (!raw) return;

      let parsed: unknown;
      try {
        parsed = load(raw);
      } catch {
        return;
      }

      if (!Array.isArray(parsed)) return;

      const lines = ['<div class="country-spirits">', "<h3>Spirits</h3>", "<ul>"];
      for (const item of parsed as SpiritItem[]) {
        if (!item || typeof item !== "object") continue;
        const name = escapeHtml(item.name ?? "Unknown");
        const type = escapeHtml(item.type ?? "neutral");
        const desc = escapeHtml(item.desc ?? "");
        const suffix = desc ? `: ${desc}` : "";
        lines.push(`<li><strong>${name}</strong> (${type})${suffix}</li>`);
      }
      lines.push("</ul>", "</div>");

      const replacement: Html = {
        type: "html",
        value: lines.join(""),
      };
      directiveParent.children[index] = replacement;
    });
  };
}
