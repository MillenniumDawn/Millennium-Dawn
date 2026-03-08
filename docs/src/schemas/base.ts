import { z } from "astro:content";

export const internalPathSchema = z
  .string()
  .regex(/^\/[A-Za-z0-9/_.-]*$/, "Expected a root-relative path");

export const hrefSchema = z
  .string()
  .refine((value) => /^(https?:\/\/|mailto:|#|\/)/i.test(value), "Expected an absolute URL or root-relative path");

export const loadingSchema = z.enum(["lazy", "eager"]);

export const slugSchema = z.string().regex(/^[a-z0-9-]+$/, "Expected a lowercase slug");

export const tocSchema = z.enum(["auto", "off"]).optional();
export const infoboxGroupKindSchema = z.enum(["default", "overview", "military_industry", "economy"]);

export const baseDocSchema = z.object({
  title: z.string(),
  description: z.string().optional(),
  permalink: internalPathSchema.optional(),
  toc: tocSchema,
  seo: z.boolean().optional(),
  robots: z.string().optional(),
  page_id: z.string().optional(),
  body_class: z.string().optional(),
  kind: z.string().optional(),
  order: z.number().int().optional(),
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
      kind: resolveInfoboxGroupKind(group.section, group.kind),
    })),
);
