import { z } from "astro/zod";
import { hrefSchema, internalPathSchema, loadingSchema } from "./base";

export const navigationSchema = z.object({
  main: z.array(
    z.object({
      title: z.string(),
      url: internalPathSchema,
    }),
  ),
  footer_docs: z.array(
    z.object({
      title: z.string(),
      url: internalPathSchema,
    }),
  ),
  social: z.array(
    z.object({
      name: z.string(),
      url: hrefSchema,
    }),
  ),
});

export const releaseSchema = z.object({
  current: z.object({
    md_version: z.string(),
    hoi_version: z.string(),
    checksum: z.string(),
  }),
  links: z.record(
    z.string(),
    z.object({
      label: z.string(),
      url: hrefSchema,
    }),
  ),
});

export const sectionsSchema = z.record(
  z.string(),
  z.object({
    title: z.string(),
    url: internalPathSchema,
  }),
);

export const homeSchema = z.object({
  hero: z.object({
    badge: z.object({
      label: z.string(),
      url: hrefSchema,
    }),
    title: z.string(),
    subtitle: z.string(),
    primary_cta: z.object({
      label: z.string(),
      url: hrefSchema,
    }),
    secondary_cta: z.object({
      label: z.string(),
      url: hrefSchema,
    }),
    community_cta: z.object({
      label: z.string(),
      url: hrefSchema,
    }),
    note: z.object({
      prefix: z.string(),
      link_label: z.string(),
      link_url: hrefSchema,
      suffix: z.string().optional(),
    }),
  }),
  roadmaps: z.array(
    z.object({
      title: z.string(),
      paragraphs: z.array(z.string()).optional(),
      image: z.object({
        src: internalPathSchema,
        alt: z.string(),
        width: z.number().int(),
        height: z.number().int(),
        loading: loadingSchema.optional(),
      }),
    }),
  ),
  team_join: z.object({
    description: z.string(),
  }),
  paratranz_projects: z.array(
    z.object({
      name: z.string(),
      url: hrefSchema,
    }),
  ),
  resource_groups: z.array(
    z.object({
      heading: z.string(),
      items: z.array(
        z.object({
          title: z.string(),
          url: hrefSchema,
        }),
      ),
    }),
  ),
  credits: z.object({
    model_credit_list: hrefSchema,
    special_thanks: z.array(
      z.object({
        text: z.string(),
      }),
    ),
  }),
});

export const devDiaryArchiveSchema = z.array(
  z.object({
    title: z.string(),
    entries: z.array(
      z.object({
        title: z.string(),
        url: hrefSchema.optional(),
        note: z.string().optional(),
      }),
    ),
  }),
);

export const knownSubmodsSchema = z.object({
  groups: z.array(
    z.object({
      title: z.string(),
      note: z.string().optional(),
      items: z.array(
        z.object({
          title: z.string(),
          url: hrefSchema,
        }),
      ),
    }),
  ),
});
