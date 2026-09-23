import type { Root } from "mdast";
import { visit } from "unist-util-visit";

const ROLE_KINDS = new Set(["junior", "developer", "senior", "inactive", "council"]);

export function remarkDevTeamRoles(): (tree: Root) => void {
  return (tree: Root): void => {
    visit(tree, (node) => {
      if (node.type !== "textDirective" || node.name !== "role") return;

      const kind = node.attributes?.kind;
      if (!kind || !ROLE_KINDS.has(kind)) return;

      const data = (node.data ??= {}) as Record<string, unknown>;
      data.hName = "span";
      data.hProperties = { className: ["dev-team-role", `dev-team-role--${kind}`] };
    });
  };
}
