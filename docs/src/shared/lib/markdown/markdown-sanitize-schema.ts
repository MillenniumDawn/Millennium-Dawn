import { defaultSchema, type Schema } from "hast-util-sanitize";

const baseAttributes = defaultSchema.attributes ?? {};

export const markdownSanitizeSchema: Schema = {
  ...defaultSchema,
  attributes: {
    ...baseAttributes,
    a: [...(baseAttributes.a ?? []), "target", "rel"],
    "*": [...(baseAttributes["*"] ?? []), "class", "className"],
  },
};
