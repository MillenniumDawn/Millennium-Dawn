import type { Element, Root } from "hast";
import { visit } from "unist-util-visit";
import type { Parent } from "unist";

export function rehypeTableWrapper(): (tree: Root) => void {
  return (tree: Root): void => {
    visit(tree, (node, index, parent) => {
      if (!parent || typeof index !== "number") return;
      if (node.type !== "element" || node.tagName !== "table") return;

      const tableNode = node;
      const tableParent = parent as Parent;
      if (
        parent.type === "element" &&
        parent.tagName === "div" &&
        parent.properties.className?.includes("table-wrapper")
      ) {
        return;
      }

      const wrapper: Element = {
        type: "element",
        tagName: "div",
        properties: { className: ["table-wrapper"] },
        children: [tableNode],
      };

      if (!Array.isArray(tableParent.children)) return;
      tableParent.children[index] = wrapper;
    });
  };
}
