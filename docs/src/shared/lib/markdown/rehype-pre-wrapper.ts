import type { Element, Root } from "hast";
import { visit } from "unist-util-visit";

function hasPreWrapperClass(parent: Element): boolean {
  const className = parent.properties?.className;
  if (!className) return false;
  const list = Array.isArray(className) ? className : [String(className)];
  return list.some((c) => String(c) === "pre-wrapper");
}

export function rehypePreWrapper(): (tree: Root) => void {
  return (tree: Root): void => {
    visit(tree, (node, index, parent) => {
      if (!parent || typeof index !== "number") return;
      if (node.type !== "element" || node.tagName !== "pre") return;

      const preParent = parent as Element;
      if (preParent.type === "element" && preParent.tagName === "div" && hasPreWrapperClass(preParent)) {
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
