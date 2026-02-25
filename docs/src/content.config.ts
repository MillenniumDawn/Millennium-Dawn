import { defineCollection, z } from "astro:content";

const tocSchema = z.enum(["auto", "off"]).optional();

const baseDocSchema = z.object({
  title: z.string(),
  description: z.string().optional(),
  permalink: z.string().optional(),
  toc: tocSchema,
  seo: z.boolean().optional(),
  robots: z.string().optional(),
  page_id: z.string().optional(),
  body_class: z.string().optional(),
  page_assets: z.array(z.string()).optional(),
  kind: z.string().optional(),
  order: z.number().int().optional(),
});

const infoboxSchema = z.array(
  z.object({
    section: z.string(),
    stats: z.array(
      z.object({
        label: z.string(),
        value: z.string(),
      }),
    ),
  }),
);

const pages = defineCollection({
  type: "content",
  schema: baseDocSchema,
});

const countries = defineCollection({
  type: "content",
  schema: baseDocSchema.extend({
    slug: z.string().optional(),
    unique_focus_tree: z.boolean().default(false),
    grid_order: z.number().int(),
    grid_note: z.string().optional(),
    flag_image: z.string().optional(),
    infobox: infoboxSchema.default([]),
  }),
});

const changelogSections = defineCollection({
  type: "content",
  schema: baseDocSchema.extend({
    page_id: z.string().optional(),
    order: z.number().int(),
    toc: z.enum(["off"]).optional(),
  }),
});

const tutorials = defineCollection({
  type: "content",
  schema: baseDocSchema,
});

const resources = defineCollection({
  type: "content",
  schema: baseDocSchema,
});

const devDiaries = defineCollection({
  type: "content",
  schema: baseDocSchema,
});

const misc = defineCollection({
  type: "content",
  schema: baseDocSchema,
});

const redirects = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    permalink: z.string(),
    redirect_to: z.string(),
    seo: z.boolean().default(false),
    robots: z.string().default("noindex, nofollow"),
    toc: z.enum(["off"]).default("off"),
    description: z.string().optional(),
  }),
});

const navigation = defineCollection({
  type: "data",
  schema: z.object({
    main: z.array(
      z.object({
        title: z.string(),
        url: z.string(),
      }),
    ),
    footer_docs: z.array(
      z.object({
        title: z.string(),
        url: z.string(),
      }),
    ),
    social: z.array(
      z.object({
        name: z.string(),
        url: z.string(),
      }),
    ),
  }),
});

const release = defineCollection({
  type: "data",
  schema: z.object({
    current: z.object({
      md_version: z.string(),
      hoi_version: z.string(),
      checksum: z.string(),
    }),
    links: z.record(
      z.object({
        label: z.string(),
        url: z.string(),
      }),
    ),
  }),
});

const sections = defineCollection({
  type: "data",
  schema: z.record(
    z.object({
      title: z.string(),
      url: z.string(),
    }),
  ),
});

const home = defineCollection({
  type: "data",
  schema: z.object({
    roadmaps: z.array(
      z.object({
        title: z.string(),
        paragraphs: z.array(z.string()).optional(),
        image: z.object({
          src: z.string(),
          alt: z.string(),
          width: z.number().int().optional(),
          height: z.number().int().optional(),
          loading: z.string().optional(),
        }),
      }),
    ),
    team_join: z.object({
      description: z.string(),
    }),
    paratranz_projects: z.array(
      z.object({
        name: z.string(),
        url: z.string(),
      }),
    ),
    resource_groups: z.array(
      z.object({
        heading: z.string(),
        items: z.array(
          z.object({
            title: z.string(),
            url: z.string(),
          }),
        ),
      }),
    ),
    credits: z.object({
      model_credit_list: z.string(),
      special_thanks: z.array(
        z.object({
          text: z.string(),
        }),
      ),
    }),
  }),
});

const devDiaryArchive = defineCollection({
  type: "data",
  schema: z.array(
    z.object({
      title: z.string(),
      entries: z.array(
        z.object({
          title: z.string(),
          url: z.string().optional(),
          note: z.string().optional(),
        }),
      ),
    }),
  ),
});

const knownSubmods = defineCollection({
  type: "data",
  schema: z.object({
    groups: z.array(
      z.object({
        title: z.string(),
        note: z.string().optional(),
        items: z.array(
          z.object({
            title: z.string(),
            url: z.string(),
          }),
        ),
      }),
    ),
  }),
});

export const collections = {
  pages,
  countries,
  changelogSections,
  tutorials,
  resources,
  devDiaries,
  misc,
  redirects,
  navigation,
  release,
  sections,
  home,
  devDiaryArchive,
  knownSubmods,
};
