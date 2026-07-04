import type { Element, Root } from "hast";
import { visit } from "unist-util-visit";

/**
 * Adds scope attribute to th elements for WCAG 1.3.1.
 * - th in thead: scope="col"
 * - th in tbody: scope="row"
 */
export function rehypeTableScope(): (tree: Root) => void {
  return (tree: Root): void => {
    visit(tree, (node, _index, parent) => {
      if (node.type !== "element" || node.tagName !== "tr") return;

      const row = node;
      const section = parent as Element;
      const scope = section?.tagName === "thead" ? "col" : section?.tagName === "tbody" ? "row" : null;
      if (!scope) return;

      if (!Array.isArray(row.children)) return;
      for (const child of row.children) {
        if (child.type === "element" && child.tagName === "th") {
          child.properties = { ...child.properties, scope };
        }
      }
    });
  };
}
