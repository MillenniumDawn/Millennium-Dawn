import type { LanguageRegistration } from "shiki";

/** Control flow and block structure keywords */
const HOISCRIPT_KEYWORDS = [
  "if",
  "else",
  "else_if",
  "elseif",
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
  "random_country",
  "random_state",
  "random_scope",
] as const;

/** Logical operators in triggers/effects */
const HOISCRIPT_LOGICAL = ["OR", "AND", "NOT"] as const;

/** Scope references and boolean literals */
const HOISCRIPT_BUILTINS = ["ROOT", "FROM", "PREV", "THIS", "yes", "no", "always"] as const;

/** Common block/entity type keywords (focus, decision, event blocks) */
const HOISCRIPT_BLOCK_TYPES = [
  "focus",
  "id",
  "allowed",
  "visible",
  "available",
  "bypass",
  "cancel",
  "complete_effect",
  "completion_reward",
  "fire_only_once",
  "major",
  "is_triggered_only",
] as const;

/** Common effects and triggers (highlighted as function-like) */
const HOISCRIPT_EFFECTS_TRIGGERS = [
  "add_ideas",
  "add_ideas_from_tech",
  "add_dynamic_modifier",
  "remove_dynamic_modifier",
  "country_event",
  "state_event",
  "add_to_variable",
  "subtract_from_variable",
  "multiply_variable",
  "divide_variable",
  "set_variable",
  "set_temp_variable",
  "add_country_modifier",
  "remove_country_modifier",
  "add_timed_idea",
  "log",
  "has_country_flag",
  "has_character_flag",
  "country_exists",
  "has_government",
  "has_autonomy_state",
  "original_tag",
  "modifier",
  "search_filters",
  "prerequisite",
  "mutually_exclusive",
  "relative_position_id",
  "ai_will_do",
  "cost",
  "days_remove",
] as const;

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
    { include: "#numbers" },
    { include: "#keywords" },
    { include: "#logical" },
    { include: "#builtins" },
    { include: "#effectsTriggers" },
    { include: "#blockTypes" },
    { include: "#countryTag" },
    { include: "#gfxRef" },
    { include: "#locKey" },
    { include: "#properties" },
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
          patterns: [
            { match: '\\\\[\\\\"nrt]', name: "constant.character.escape.hoiscript" },
            { match: "£[A-Za-z0-9_]+", name: "constant.other.placeholder.hoiscript" },
          ],
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
    numbers: {
      patterns: [{ match: "\\b-?\\d+(?:\\.\\d+)?\\b", name: "constant.numeric.hoiscript" }],
    },
    keywords: {
      patterns: [{ match: toWordPattern(HOISCRIPT_KEYWORDS), name: "keyword.control.hoiscript" }],
    },
    logical: {
      patterns: [{ match: toWordPattern(HOISCRIPT_LOGICAL), name: "keyword.operator.logical.hoiscript" }],
    },
    builtins: {
      patterns: [{ match: toWordPattern(HOISCRIPT_BUILTINS), name: "constant.language.hoiscript" }],
    },
    effectsTriggers: {
      patterns: [
        {
          match: `\\b(${HOISCRIPT_EFFECTS_TRIGGERS.join("|")})\\b(?=\\s*=)`,
          captures: {
            1: { name: "entity.name.function.hoiscript" },
          },
        },
      ],
    },
    blockTypes: {
      patterns: [
        {
          match: `\\b(${HOISCRIPT_BLOCK_TYPES.join("|")})\\b(?=\\s*=)`,
          captures: {
            1: { name: "storage.type.hoiscript" },
          },
        },
      ],
    },
    countryTag: {
      patterns: [
        {
          match: "\\b([A-Z][A-Z0-9]{2})(?=\\s*=\\s*\\{)",
          captures: {
            1: { name: "constant.other.country-tag.hoiscript" },
          },
        },
      ],
    },
    gfxRef: {
      patterns: [
        {
          match: "\\b(GFX_[A-Za-z0-9_]+)\\b",
          captures: {
            1: { name: "constant.other.asset.hoiscript" },
          },
        },
        {
          match: "\\b(CAT_[A-Za-z0-9_]+)\\b",
          captures: {
            1: { name: "constant.other.asset.hoiscript" },
          },
        },
      ],
    },
    locKey: {
      patterns: [
        {
          match: "\\b([A-Za-z][A-Za-z0-9_]*\\.[a-z0-9_.]+)\\b",
          captures: {
            1: { name: "entity.name.tag.hoiscript" },
          },
        },
      ],
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
    operators: {
      patterns: [
        { match: "=", name: "keyword.operator.assignment.hoiscript" },
        { match: ">=|<=|>|<|!=|==", name: "keyword.operator.comparison.hoiscript" },
      ],
    },
    punctuation: {
      patterns: [{ match: "[{}()\\[\\],.;]", name: "punctuation.section.block.hoiscript" }],
    },
  },
};
