import { visit } from "unist-util-visit";

type HastElement = {
  type: "element";
  tagName: string;
  properties?: Record<string, unknown>;
  children?: HastNode[];
};

type HastNode = HastElement | { type: string; [key: string]: unknown };

function hasClassName(node: HastElement, className: string): boolean {
  const value = node.properties?.className;
  if (typeof value === "string") return value.split(/\s+/).includes(className);
  if (Array.isArray(value)) return value.map(String).includes(className);
  return false;
}

export function rehypeTableWrapper() {
  return (tree: unknown) => {
    visit(tree as any, "element", (node: HastNode, index: number | undefined, parent: HastElement | undefined) => {
      if (!parent || typeof index !== "number") return;
      if (node.type !== "element" || node.tagName !== "table") return;

      if (parent.type === "element" && parent.tagName === "div" && hasClassName(parent, "table-wrapper")) {
        return;
      }

      const wrapper: HastElement = {
        type: "element",
        tagName: "div",
        properties: { className: ["table-wrapper"] },
        children: [node],
      };

      if (!Array.isArray(parent.children)) return;
      parent.children[index] = wrapper;
    });
  };
}
