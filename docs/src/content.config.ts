import { defineCollection, z } from "astro:content";
import { glob } from "astro/loaders";
import { baseDocSchema, infoboxSchema, internalPathSchema, slugSchema } from "./schemas/base";
import {
  devDiaryArchiveSchema,
  homeSchema,
  knownSubmodsSchema,
  navigationSchema,
  releaseSchema,
  sectionsSchema,
} from "./schemas/data";

const pages = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/pages" }),
  schema: baseDocSchema,
});

const countries = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/countries" }),
  schema: baseDocSchema.extend({
    slug: slugSchema.optional(),
    unique_focus_tree: z.boolean().default(false),
    grid_order: z.number().int(),
    grid_note: z.string().optional(),
    flag_image: internalPathSchema.optional(),
    infobox: infoboxSchema.default([]),
  }),
});

const changelogSections = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/changelogSections" }),
  schema: baseDocSchema.extend({
    page_id: z.string().optional(),
    order: z.number().int(),
    toc: z.enum(["off"]).optional(),
  }),
});

const tutorials = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/tutorials" }),
  schema: baseDocSchema,
});

const resources = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/resources" }),
  schema: baseDocSchema,
});

const devDiaries = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/devDiaries" }),
  schema: baseDocSchema,
});

const misc = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/misc" }),
  schema: baseDocSchema,
});

const redirects = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/redirects" }),
  schema: z.object({
    title: z.string(),
    permalink: internalPathSchema,
    redirect_to: internalPathSchema,
    seo: z.boolean().default(false),
    robots: z.string().default("noindex, nofollow"),
    toc: z.enum(["off"]).default("off"),
    description: z.string().optional(),
  }),
});

const navigation = defineCollection({
  loader: glob({ pattern: "**/*.yml", base: "./src/content/navigation" }),
  schema: navigationSchema,
});

const release = defineCollection({
  loader: glob({ pattern: "**/*.yml", base: "./src/content/release" }),
  schema: releaseSchema,
});

const sections = defineCollection({
  loader: glob({ pattern: "**/*.yml", base: "./src/content/sections" }),
  schema: sectionsSchema,
});

const home = defineCollection({
  loader: glob({ pattern: "**/*.yml", base: "./src/content/home" }),
  schema: homeSchema,
});

const devDiaryArchive = defineCollection({
  loader: glob({ pattern: "**/*.yml", base: "./src/content/devDiaryArchive" }),
  schema: devDiaryArchiveSchema,
});

const knownSubmods = defineCollection({
  loader: glob({ pattern: "**/*.yml", base: "./src/content/knownSubmods" }),
  schema: knownSubmodsSchema,
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
