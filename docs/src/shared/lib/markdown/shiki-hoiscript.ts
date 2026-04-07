import type { LanguageRegistration } from "shiki";

/**
 * HOI4 / Paradox script syntax highlighting aligned with
 * https://github.com/AngriestBird/kate-paradox-hoi4-syntax (Kate KSyntaxHighlighting).
 * Same categories and token roles for consistent look.
 */

const BOOLEANS = ["yes", "no"] as const;

const SCOPES = [
	"ROOT",
	"THIS",
	"FROM",
	"PREV",
	"OVERLORD",
	"FACTION_LEADER",
	"CAPITAL",
	"OWNER",
	"CONTROLLER",
] as const;

const EFFECTS = [
	"add_ideas",
	"remove_ideas",
	"add_equipment_to_stockpile",
	"add_manpower",
	"add_political_power",
	"add_stability",
	"add_war_support",
	"add_opinion_modifier",
	"add_relation_modifier",
	"add_state_claim",
	"add_state_core",
	"add_tech_bonus",
	"add_timed_idea",
	"add_to_faction",
	"add_to_variable",
	"annex_country",
	"capital_scope",
	"clamp_variable",
	"country_event",
	"create_country_leader",
	"create_faction",
	"custom_effect_tooltip",
	"declare_war_on",
	"division_template",
	"effect_tooltip",
	"every_country",
	"every_owned_state",
	"every_state",
	"hidden_effect",
	"if",
	"else_if",
	"else",
	"load_focus_tree",
	"mark_focus_tree_layout_dirty",
	"news_event",
	"random_country",
	"random_list",
	"random_owned_state",
	"release_autonomy",
	"remove_from_faction",
	"remove_opinion_modifier",
	"remove_relation_modifier",
	"set_autonomy",
	"set_capital",
	"set_country_flag",
	"set_global_flag",
	"set_politics",
	"set_popularities",
	"set_state_flag",
	"set_technology",
	"set_variable",
	"start_civil_war",
	"state_event",
	"transfer_state",
	"unlock_decision_tooltip",
	"white_peace",
] as const;

const TRIGGERS = [
	"always",
	"AND",
	"OR",
	"NOT",
	"can_declare_war_on",
	"check_variable",
	"controls_state",
	"date",
	"enemies_strength_ratio",
	"focus_progress",
	"has_capitulated",
	"has_country_flag",
	"has_dlc",
	"has_equipment",
	"has_global_flag",
	"has_government",
	"has_idea",
	"has_non_aggression_pact_with",
	"has_opinion",
	"has_political_power",
	"has_stability",
	"has_state_flag",
	"has_tech",
	"has_trade_embargo_with_us",
	"has_war",
	"has_war_support",
	"has_war_with",
	"is_ally_with",
	"is_faction_leader",
	"is_fully_controlled_by",
	"is_in_faction",
	"is_in_faction_with",
	"is_neighbor_of",
	"is_owned_and_controlled_by",
	"is_puppet",
	"is_puppet_of",
	"is_subject",
	"is_subject_of",
	"manpower",
	"num_divisions",
	"original_tag",
	"owns_state",
	"stability",
	"strength_ratio",
	"tag",
	"threat",
] as const;

const KEYWORDS = [
	"focus",
	"id",
	"icon",
	"cost",
	"x",
	"y",
	"relative_position_id",
	"prerequisite",
	"mutually_exclusive",
	"bypass",
	"available",
	"cancel_if_invalid",
	"continue_if_invalid",
	"completion_reward",
	"search_filters",
	"ai_will_do",
	"will_lead_to_war_with",
	"select_effect",
	"name",
	"desc",
	"picture",
	"allowed",
	"allowed_civil_war",
	"cancel",
	"modifier",
	"targeted_modifier",
	"rule",
	"research_bonus",
	"equipment_bonus",
	"traits",
	"factor",
	"add",
	"base",
	"value",
	"token",
	"limit",
	"chance",
	"days",
	"hours",
	"random",
	"mean_time_to_happen",
	"trigger",
	"option",
	"title",
	"fire_only_once",
	"is_triggered_only",
	"immediate",
	"hidden",
	"major",
	"province",
	"state",
	"color",
	"colors",
	"frames",
	"ribbon",
	"category",
	"path",
	"research_cost",
	"start_year",
	"folder",
	"enable",
	"on_research_complete",
	"ai_research_weights",
	"dependencies",
	"sub_technologies",
	"doctrine",
	"type",
	"parent",
	"gfx_type",
	"group",
	"division_types",
	"position",
	"map_icon_category",
	"priority",
	"active",
	"default",
] as const;

function toWordPattern(words: readonly string[]): string {
	return `\\b(?:${words.join("|")})\\b`;
}

export const hoiscriptLanguage: LanguageRegistration = {
	name: "hoiscript",
	displayName: "HOI4 Script",
	scopeName: "source.hoiscript",
	aliases: ["hoi", "hoi4", "paradox-script"],
	patterns: [
		{ include: "#comments" },
		{ include: "#strings" },
		{ include: "#numbers" },
		{ include: "#booleans" },
		{ include: "#scopes" },
		{ include: "#effects" },
		{ include: "#triggers" },
		{ include: "#keywords" },
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
			],
		},
		numbers: {
			patterns: [
				{
					match: "\\b-?\\d+(?:\\.\\d+)?\\b",
					name: "constant.numeric.hoiscript",
				},
			],
		},
		booleans: {
			patterns: [
				{
					match: toWordPattern([...BOOLEANS]),
					name: "constant.language.boolean.hoiscript",
				},
			],
		},
		scopes: {
			patterns: [
				{
					match: toWordPattern([...SCOPES]),
					name: "constant.language.scope.hoiscript",
				},
			],
		},
		effects: {
			patterns: [
				{
					match: toWordPattern([...EFFECTS]),
					name: "entity.name.function.hoiscript",
				},
			],
		},
		triggers: {
			patterns: [
				{
					match: toWordPattern([...TRIGGERS]),
					name: "entity.other.attribute.name.hoiscript",
				},
			],
		},
		keywords: {
			patterns: [
				{
					match: toWordPattern([...KEYWORDS]),
					name: "keyword.other.hoiscript",
				},
			],
		},
		countryTag: {
			patterns: [
				{
					match: "\\b[A-Z][A-Z0-9]{1,2}\\b",
					name: "variable.other.hoiscript",
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
			patterns: [
				{
					match: "[{}()\\[\\],.;]",
					name: "punctuation.section.block.hoiscript",
				},
			],
		},
	},
};
