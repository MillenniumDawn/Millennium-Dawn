import { getCollection, getEntry } from "astro:content";
import { stripMarkdownExt } from "./slugs";

export interface OgPageData {
  slug: string;
  title: string;
  description: string;
}

const DEFAULT_DESCRIPTION =
  "Documentation for the Millennium Dawn: A Modern Day mod for the game Hearts of Iron IV.";

async function getStaticPages(): Promise<OgPageData[]> {
  const pages: OgPageData[] = [
    {
      slug: "index",
      title: "Home",
      description: DEFAULT_DESCRIPTION,
    },
    {
      slug: "changelogs",
      title: "Changelogs",
      description: "Changelogs for Millennium Dawn: A Modern Day Mod",
    },
    {
      slug: "dev-diaries",
      title: "Dev Diaries",
      description:
        "Development diaries from the Millennium Dawn mod team, covering new features, changes, and updates.",
    },
    {
      slug: "tutorials",
      title: "Tutorials",
      description:
        "Guides and tutorials for playing Millennium Dawn: A Modern Day mod for Hearts of Iron IV.",
    },
    {
      slug: "support",
      title: "Technical Support",
      description:
        "Technical support and troubleshooting help for Millennium Dawn: A Modern Day mod for Hearts of Iron IV.",
    },
    {
      slug: "resources",
      title: "Resources",
      description: "List of resources for the development team of Millennium Dawn.",
    },
  ];

  // Content-backed static pages (served via index.astro with getEntry)
  const contentPageIds = [
    { id: "getting-started", route: "getting-started" },
    { id: "faq", route: "faq" },
    { id: "countries", route: "countries" },
  ] as const;

  for (const { id, route } of contentPageIds) {
    const entry = await getEntry("pages", id);
    if (entry) {
      pages.push({
        slug: route,
        title: entry.data.title,
        description: entry.data.description ?? DEFAULT_DESCRIPTION,
      });
    }
  }

  return pages;
}

async function collectDynamicPages(): Promise<OgPageData[]> {
  const pages: OgPageData[] = [];

  const [
    countryEntries,
    changelogEntries,
    devDiaryEntries,
    tutorialEntries,
    resourceEntries,
    miscEntries,
  ] = await Promise.all([
    getCollection("countries"),
    getCollection("changelogSections"),
    getCollection("devDiaries"),
    getCollection("tutorials"),
    getCollection("resources"),
    getCollection("misc"),
  ]);

  for (const entry of countryEntries) {
    const slug = entry.data.slug ?? stripMarkdownExt(entry.id);
    pages.push({
      slug: `countries/${slug}`,
      title: entry.data.title,
      description: entry.data.description ?? DEFAULT_DESCRIPTION,
    });
  }

  for (const entry of changelogEntries) {
    if (entry.data.seo === false) continue;
    pages.push({
      slug: `changelogs/${stripMarkdownExt(entry.id)}`,
      title: entry.data.title,
      description: entry.data.description ?? DEFAULT_DESCRIPTION,
    });
  }

  for (const entry of devDiaryEntries) {
    if (entry.data.seo === false) continue;
    const slug = entry.data.permalink
      ? entry.data.permalink.replace(/^\/+|\/+$/g, "")
      : `dev-diaries/${stripMarkdownExt(entry.id)}`;
    pages.push({
      slug,
      title: entry.data.title,
      description: entry.data.description ?? DEFAULT_DESCRIPTION,
    });
  }

  for (const entry of tutorialEntries) {
    if (entry.data.seo === false) continue;
    pages.push({
      slug: `player-tutorials/${stripMarkdownExt(entry.id)}`,
      title: entry.data.title,
      description: entry.data.description ?? DEFAULT_DESCRIPTION,
    });
  }

  for (const entry of resourceEntries) {
    if (entry.data.seo === false) continue;
    pages.push({
      slug: `dev-resources/${stripMarkdownExt(entry.id)}`,
      title: entry.data.title,
      description: entry.data.description ?? DEFAULT_DESCRIPTION,
    });
  }

  for (const entry of miscEntries) {
    if (entry.data.seo === false) continue;
    pages.push({
      slug: `misc/${stripMarkdownExt(entry.id)}`,
      title: entry.data.title,
      description: entry.data.description ?? DEFAULT_DESCRIPTION,
    });
  }

  return pages;
}

export async function getAllOgPages(): Promise<OgPageData[]> {
  const [staticPages, dynamicPages] = await Promise.all([
    getStaticPages(),
    collectDynamicPages(),
  ]);
  return [...staticPages, ...dynamicPages];
}
