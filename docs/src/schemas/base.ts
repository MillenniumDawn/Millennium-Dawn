import { z } from "astro/zod";

export const internalPathSchema = z.string().regex(/^\/[A-Za-z0-9/_.-]*$/, "Expected a root-relative path");

export const hrefSchema = z
  .string()
  .refine((value) => /^(https?:\/\/|mailto:|#|\/)/i.test(value), "Expected an absolute URL or root-relative path");

export const loadingSchema = z.enum(["lazy", "eager"]);

export const slugSchema = z.string().regex(/^[a-z0-9-]+$/, "Expected a lowercase slug");

export const tocSchema = z.enum(["auto", "off"]).optional();
export const infoboxGroupKindSchema = z.enum(["default", "overview", "military_industry", "economy"]);
export const infoboxStatKeySchema = z.enum([
  "tag",
  "divisions",
  "total_factories",
  "military_industry",
  "civilian_industry",
  "naval_dockyards",
  "treasury",
  "debt",
  "investments",
]);

export const baseDocSchema = z.object({
  title: z.string(),
  description: z.string().optional(),
  permalink: internalPathSchema.optional(),
  toc: tocSchema,
  seo: z.boolean().optional(),
  robots: z.string().optional(),
  page_id: z.string().optional(),
  body_class: z.string().optional(),
  hidden: z.boolean().optional(),
  kind: z.string().optional(),
  order: z.number().int().optional(),
  last_updated: z.coerce.date().optional(),
});

function resolveInfoboxGroupKind(
  section: string,
  kind?: z.infer<typeof infoboxGroupKindSchema>,
): z.infer<typeof infoboxGroupKindSchema> {
  if (kind) return kind;

  const normalizedSection = section.toLowerCase();
  if (normalizedSection === "overview") return "overview";
  if (normalizedSection.includes("military") && normalizedSection.includes("industry")) {
    return "military_industry";
  }
  if (normalizedSection.includes("economy")) return "economy";
  return "default";
}

function normalizeInfoboxLabel(label: string): string {
  return label.trim().toLowerCase().replace(/\./g, "").replace(/\s+/g, " ");
}

function resolveInfoboxStatKey(label: string): z.infer<typeof infoboxStatKeySchema> | undefined {
  const normalized = normalizeInfoboxLabel(label);

  switch (normalized) {
    case "tag":
      return "tag";
    case "divisions":
      return "divisions";
    case "total factories":
      return "total_factories";
    case "military ind":
      return "military_industry";
    case "civilian ind":
      return "civilian_industry";
    case "naval dockyards":
      return "naval_dockyards";
    case "treasury":
      return "treasury";
    case "debt":
      return "debt";
    case "investments":
      return "investments";
    default:
      return undefined;
  }
}

export const infoboxSchema = z.array(
  z
    .object({
      section: z.string(),
      kind: infoboxGroupKindSchema.optional(),
      stats: z.array(
        z.object({
          label: z.string(),
          value: z.string(),
        }),
      ),
    })
    .transform((group) => ({
      ...group,
      stats: group.stats.map((stat) => ({
        ...stat,
        key: resolveInfoboxStatKey(stat.label),
      })),
      kind: resolveInfoboxGroupKind(group.section, group.kind),
    })),
);
