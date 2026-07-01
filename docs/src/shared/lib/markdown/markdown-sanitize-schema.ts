import { defaultSchema, type Schema } from "hast-util-sanitize";

const baseAttributes = defaultSchema.attributes ?? {};

/**
 * GFM defaults put restrictive `className` tuples first (h2: sr-only; lists: task-list).
 * `findDefinition` returns the first match, so permissive `className` must precede those tuples.
 */
function allowTailwindClasses(tag: "h2" | "ul" | "ol" | "li") {
  return ["className", "class", ...(baseAttributes[tag] ?? [])];
}

export const markdownSanitizeSchema: Schema = {
  ...defaultSchema,
  attributes: {
    ...baseAttributes,
    a: [...(baseAttributes.a ?? []), "target", "rel"],
    h2: allowTailwindClasses("h2"),
    ul: allowTailwindClasses("ul"),
    ol: allowTailwindClasses("ol"),
    li: allowTailwindClasses("li"),
    "*": [...(baseAttributes["*"] ?? []), "class", "className"],
  },
};
