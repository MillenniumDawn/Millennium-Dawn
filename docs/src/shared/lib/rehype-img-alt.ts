import type { Root } from "hast";
import { visit } from "unist-util-visit";

/**
 * Ensures images with empty or missing alt are marked as decorative
 * for WCAG 1.1.1 - adds role="presentation" and aria-hidden when alt is empty.
 */
export function rehypeImgAlt(): (tree: Root) => void {
  return (tree: Root): void => {
    visit(tree, (node) => {
      if (node.type !== "element" || node.tagName !== "img") return;

      const el = node;
      const alt = el.properties?.alt;
      const hasAlt = typeof alt === "string" && alt.trim().length > 0;

      if (!hasAlt) {
        el.properties = {
          ...el.properties,
          role: "presentation",
          "aria-hidden": "true",
        };
      }
    });
  };
}
