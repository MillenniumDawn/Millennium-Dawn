import type { Element, Root } from "hast";
import { visit } from "unist-util-visit";
import type { Parent } from "unist";

export function rehypePreWrapper(): (tree: Root) => void {
  return (tree: Root): void => {
    visit(tree, (node, index, parent) => {
      if (!parent || typeof index !== "number") return;
      if (node.type !== "element" || node.tagName !== "pre") return;

      const preParent = parent as Parent;
      if (
        preParent.type === "element" &&
        preParent.tagName === "div" &&
        (preParent as Element).properties?.className &&
        Array.isArray((preParent as Element).properties.className) &&
        (preParent as Element).properties.className.includes("pre-wrapper")
      ) {
        return;
      }

      const wrapper: Element = {
        type: "element",
        tagName: "div",
        properties: { className: ["pre-wrapper"] },
        children: [node],
      };

      if (!Array.isArray(preParent.children)) return;
      preParent.children[index] = wrapper;
    });
  };
}
