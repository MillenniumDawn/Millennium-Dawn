import type { LanguageRegistration } from "shiki";

const HOISCRIPT_KEYWORDS = [
  "if",
  "else",
  "else_if",
  "limit",
  "hidden_effect",
  "trigger",
  "effect",
  "random_list",
  "random_owned_state",
  "every_country",
  "any_country",
  "every_state",
  "any_state",
  "every_owned_state",
  "any_owned_state",
  "every_unit_leader",
  "any_unit_leader",
  "set_variable",
  "add_to_variable",
  "subtract_from_variable",
  "multiply_variable",
  "divide_variable",
  "set_temp_variable",
  "country_event",
  "state_event",
  "add_dynamic_modifier",
  "remove_dynamic_modifier",
] as const;

const HOISCRIPT_BUILTINS = ["ROOT", "FROM", "PREV", "THIS", "yes", "no", "always"] as const;

function toWordPattern(words: readonly string[]): string {
  return `\\b(?:${words.join("|")})\\b`;
}

export const hoiscriptLanguage: LanguageRegistration = {
  name: "hoiscript",
  displayName: "HOI Script",
  scopeName: "source.hoiscript",
  aliases: ["hoi", "hoi4", "paradox-script"],
  patterns: [
    { include: "#comments" },
    { include: "#strings" },
    { include: "#keywords" },
    { include: "#builtins" },
    { include: "#properties" },
    { include: "#numbers" },
    { include: "#operators" },
    { include: "#punctuation" },
  ],
  repository: {
    comments: {
      patterns: [
        {
          begin: "#",
          beginCaptures: {
            0: { name: "punctuation.definition.comment.hoiscript" },
          },
          end: "$",
          name: "comment.line.number-sign.hoiscript",
        },
      ],
    },
    strings: {
      patterns: [
        {
          begin: '"',
          beginCaptures: {
            0: { name: "punctuation.definition.string.begin.hoiscript" },
          },
          end: '"',
          endCaptures: {
            0: { name: "punctuation.definition.string.end.hoiscript" },
          },
          name: "string.quoted.double.hoiscript",
          patterns: [{ match: "\\\\.", name: "constant.character.escape.hoiscript" }],
        },
        {
          begin: "'",
          beginCaptures: {
            0: { name: "punctuation.definition.string.begin.hoiscript" },
          },
          end: "'",
          endCaptures: {
            0: { name: "punctuation.definition.string.end.hoiscript" },
          },
          name: "string.quoted.single.hoiscript",
          patterns: [{ match: "\\\\.", name: "constant.character.escape.hoiscript" }],
        },
      ],
    },
    keywords: {
      patterns: [{ match: toWordPattern(HOISCRIPT_KEYWORDS), name: "keyword.control.hoiscript" }],
    },
    builtins: {
      patterns: [{ match: toWordPattern(HOISCRIPT_BUILTINS), name: "constant.language.hoiscript" }],
    },
    properties: {
      patterns: [
        {
          match: "\\b([A-Za-z_][A-Za-z0-9_.-]*)(?=\\s*=)",
          captures: {
            1: { name: "variable.other.property.hoiscript" },
          },
        },
      ],
    },
    numbers: {
      patterns: [{ match: "\\b\\d+(?:\\.\\d+)?\\b", name: "constant.numeric.hoiscript" }],
    },
    operators: {
      patterns: [{ match: "=", name: "keyword.operator.assignment.hoiscript" }],
    },
    punctuation: {
      patterns: [{ match: "[{}()\\[\\],]", name: "punctuation.section.block.hoiscript" }],
    },
  },
};
