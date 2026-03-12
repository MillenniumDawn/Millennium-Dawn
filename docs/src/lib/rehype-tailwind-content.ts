import type { Element, Root } from "hast";
import { visit } from "unist-util-visit";
import { MARKDOWN_CLASSNAMES } from "../shared/ui/tailwind";

function asClassList(value: unknown): string[] {
  if (Array.isArray(value)) return value.map(String);
  if (typeof value === "string") return value.split(/\s+/).filter(Boolean);
  return [];
}

function addClasses(node: Element, ...classNames: (string | false | null | undefined)[]): void {
  const existing = asClassList(node.properties?.className);
  const next = new Set(existing);

  classNames
    .flatMap((value) => (typeof value === "string" ? value.split(/\s+/).filter(Boolean) : []))
    .forEach((className) => next.add(className));

  node.properties = {
    ...(node.properties ?? {}),
    className: Array.from(next),
  };
}

function tagNameOf(node: Element | null | undefined): string | null {
  return node?.tagName ?? null;
}

export function rehypeTailwindContent(): (tree: Root) => void {
  return (tree: Root): void => {
    visit(tree, (node, index, parent) => {
      if (node.type !== "element") return;

      const tagName = node.tagName;
      const parentTag = tagNameOf(parent as Element | undefined);

      if (/^h[1-6]$/.test(tagName)) {
        const key = tagName as keyof Pick<typeof MARKDOWN_CLASSNAMES, "h1" | "h2" | "h3" | "h4" | "h5" | "h6">;
        addClasses(node, MARKDOWN_CLASSNAMES[key], "scroll-mt-[calc(var(--header-height)+1rem)]");
        return;
      }

      if (tagName === "p") {
        addClasses(node, MARKDOWN_CLASSNAMES.p, parentTag === "blockquote" && typeof index === "number" && parent?.children
          && index === parent.children.length - 1
          ? "mb-0"
          : "");
        return;
      }

      if (tagName === "a") {
        addClasses(node, MARKDOWN_CLASSNAMES.a);
        return;
      }

      if (tagName === "ul") {
        addClasses(node, MARKDOWN_CLASSNAMES.ul);
        return;
      }

      if (tagName === "ol") {
        addClasses(node, MARKDOWN_CLASSNAMES.ol);
        return;
      }

      if (tagName === "li") {
        addClasses(node, MARKDOWN_CLASSNAMES.li);
        return;
      }

      if (tagName === "hr") {
        addClasses(node, MARKDOWN_CLASSNAMES.hr);
        return;
      }

      if (tagName === "blockquote") {
        addClasses(node, MARKDOWN_CLASSNAMES.blockquote);
        return;
      }

      if (tagName === "pre") {
        addClasses(node, MARKDOWN_CLASSNAMES.pre);
        return;
      }

      if (tagName === "code") {
        addClasses(node, parentTag === "pre" ? MARKDOWN_CLASSNAMES.codeBlock : MARKDOWN_CLASSNAMES.inlineCode);
        return;
      }

      if (tagName === "details") {
        addClasses(node, MARKDOWN_CLASSNAMES.details);
        return;
      }

      if (tagName === "summary") {
        addClasses(node, MARKDOWN_CLASSNAMES.summary);
        return;
      }

      if (tagName === "table") {
        addClasses(node, MARKDOWN_CLASSNAMES.table);
        return;
      }

      if (tagName === "thead") {
        addClasses(node, MARKDOWN_CLASSNAMES.thead);
        return;
      }

      if (tagName === "tr" && parentTag === "tbody" && typeof index === "number") {
        addClasses(node, index % 2 === 0 ? "bg-table-row-odd" : "bg-table-row-even");
        return;
      }

      if (tagName === "th") {
        addClasses(node, MARKDOWN_CLASSNAMES.th);
        return;
      }

      if (tagName === "td") {
        addClasses(node, MARKDOWN_CLASSNAMES.td);
        return;
      }

      if (tagName === "img") {
        addClasses(node, MARKDOWN_CLASSNAMES.image);
        return;
      }

      if (tagName === "div") {
        const classNames = asClassList(node.properties?.className);
        if (classNames.includes("table-wrapper")) {
          addClasses(node, MARKDOWN_CLASSNAMES.tableWrapper);
          return;
        }

        if (classNames.includes("dev-diary-gallery")) {
          addClasses(node, "grid w-full grid-cols-1 gap-md my-lg tablet:grid-cols-2");
          return;
        }
      }

      if (parentTag === "details" && tagName !== "summary") {
        addClasses(
          node,
          "px-lg",
          typeof index === "number" && index === 1 ? "pt-md" : "",
          typeof index === "number" && parent?.children && index === parent.children.length - 1 ? "pb-md" : "",
        );
      }
    });
  };
}
