import { load } from "js-yaml";
import { toString } from "mdast-util-to-string";
import { visit } from "unist-util-visit";

type SpiritItem = {
  name?: string;
  type?: string;
  desc?: string;
};

function escapeHtml(value: unknown): string {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function remarkCountryDirectives() {
  return (tree: unknown) => {
    visit(tree as any, "containerDirective", (node: any, index: number | undefined, parent: any) => {
      if (!parent || typeof index !== "number") return;
      if (node.name !== "spirits") return;

      const raw = toString(node).trim();
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
        const name = escapeHtml(item.name || "Unknown");
        const type = escapeHtml(item.type || "neutral");
        const desc = escapeHtml(item.desc || "");
        const suffix = desc ? `: ${desc}` : "";
        lines.push(`<li><strong>${name}</strong> (${type})${suffix}</li>`);
      }
      lines.push("</ul>", "</div>");

      parent.children[index] = {
        type: "html",
        value: lines.join(""),
      };
    });
  };
}
