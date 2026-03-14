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

const SPIRITS_CONTAINER_CLASS = "my-xl rounded-lg border border-border-light bg-surface p-lg shadow-sm";
const SPIRITS_TITLE_CLASS =
  "mb-md text-[clamp(1.15rem,1.5vw+0.3rem,1.5rem)] font-bold leading-heading text-text-secondary";
const SPIRITS_LIST_CLASS = "m-0 flex list-none flex-wrap gap-sm p-0";
const SPIRIT_ITEM_BASE_CLASS =
  "mb-0 inline-flex items-center gap-[0.4em] rounded border px-[0.75em] py-[0.35em] text-[0.9rem] font-medium";
const SPIRIT_DESC_CLASS = "text-[0.8rem] text-text-muted";

const SPIRIT_TYPE_CLASSES: Record<string, string> = {
  positive:
    "border-[color:color-mix(in_srgb,var(--color-success)_30%,transparent)] bg-[color:color-mix(in_srgb,var(--color-success)_12%,transparent)] text-success",
  negative:
    "border-[color:color-mix(in_srgb,var(--color-danger)_30%,transparent)] bg-[color:color-mix(in_srgb,var(--color-danger)_12%,transparent)] text-danger",
  mixed:
    "border-[color:color-mix(in_srgb,var(--color-warning)_30%,transparent)] bg-[color:color-mix(in_srgb,var(--color-warning)_12%,transparent)] text-warning",
  neutral:
    "border-[color:color-mix(in_srgb,var(--color-info)_30%,transparent)] bg-[color:color-mix(in_srgb,var(--color-info)_12%,transparent)] text-text-secondary",
};

const SPIRIT_INDICATOR_CLASSES: Record<string, string> = {
  positive: "bg-success",
  negative: "bg-danger",
  mixed: "bg-warning",
  neutral: "bg-info",
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

      const lines = [
        `<div class="${SPIRITS_CONTAINER_CLASS}">`,
        `<h3 class="${SPIRITS_TITLE_CLASS}">Spirits</h3>`,
        `<ul class="${SPIRITS_LIST_CLASS}">`,
      ];
      for (const item of parsed as SpiritItem[]) {
        if (!item || typeof item !== "object") continue;
        const name = escapeHtml(item.name ?? "Unknown");
        const rawType = escapeHtml(item.type ?? "neutral");
        const normalizedType = rawType.toLowerCase();
        const desc = escapeHtml(item.desc ?? "");
        const typeClasses = SPIRIT_TYPE_CLASSES[normalizedType] ?? SPIRIT_TYPE_CLASSES.neutral;
        const indicatorClasses = SPIRIT_INDICATOR_CLASSES[normalizedType] ?? SPIRIT_INDICATOR_CLASSES.neutral;
        const descHtml = desc ? ` <span class="${SPIRIT_DESC_CLASS}">${desc}</span>` : "";
        lines.push(
          `<li class="${SPIRIT_ITEM_BASE_CLASS} ${typeClasses}"><span class="size-2 rounded-full ${indicatorClasses}"></span><strong>${name}</strong> <span class="text-[0.85rem] opacity-90">(${rawType})</span>${descHtml}</li>`,
        );
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
